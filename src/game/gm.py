"""GM-LLM — interpretador de ações livres como Game Master.

Recebe prompt em prosa do jogador + contexto do estado. Retorna interpretação
estruturada (`GMInterpretation`): classificação, plausibilidade, métricas
afetadas, side_effects, success_p, narrative_seed.

Quatro guardrails:
1. Rubrica de magnitude conservadora (no prompt).
2. CATEGORY_CAPS (clipa após retorno).
3. success_p + roll determinístico (falha total ou parcial).
4. Logging estruturado em runs/game_{id}/gm_log.jsonl.

A classe abstrata `GameMaster` define a interface; `GeminiGameMaster` é a
implementação real. Tests usam `MockGameMaster` (em conftest) para evitar
chamada de rede.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.chronicler.gemini_client import SAFETY_SETTINGS
from src.chronicler.retry import (
    MalformedResponseError,
    PermanentError,
    SafetyFilterError,
    TransientError,
)
from src.game.config import CATEGORY_CAPS, list_available_metrics
from src.game.models import GMInterpretation

logger = logging.getLogger(__name__)


GM_PROMPT_PATH = Path(__file__).parent / "prompts" / "gm_prompt_pt_br.txt"
GM_DEFAULT_MODEL = "gemini-2.5-flash"
GM_DEFAULT_TEMPERATURE = 0.7  # mais conservador que cronista (0.85)


# ---------------------------------------------------------------------------- roll determinístico


def _hash_action(action_text: str) -> str:
    """Hash estável (curto) do texto da ação — entra no seed do roll."""
    return hashlib.sha256(action_text.encode("utf-8")).hexdigest()[:16]


def roll_outcome(
    success_p: float, seed: int, turn: int, action_hash: str
) -> Tuple[float, str]:
    """Sorteia outcome de forma determinística dado (seed, turn, action_hash).

    Retorna (roll, outcome). Outcome é um de:
    - "success": roll < success_p (efeito integral)
    - "partial_failure": roll < success_p + (1-success_p)*0.5
    - "total_failure": resto

    Determinismo total: mesma tupla (seed, turn, action_hash) → mesmo roll.
    """
    # Combina os três numa string e hasheia para inteiro estável (não depende
    # de Python-internal hash randomization).
    combined = f"{seed}:{turn}:{action_hash}".encode("utf-8")
    rng_seed = int(hashlib.sha256(combined).hexdigest()[:8], 16)
    rng = np.random.default_rng(rng_seed)
    roll = float(rng.random())
    if roll < success_p:
        return roll, "success"
    if roll < success_p + (1.0 - success_p) * 0.5:
        return roll, "partial_failure"
    return roll, "total_failure"


# ---------------------------------------------------------------------------- clip


def clip_interpretation(
    interp: GMInterpretation,
) -> Tuple[GMInterpretation, List[str]]:
    """Aplica CATEGORY_CAPS — clipa magnitudes que excedem.

    Retorna (interp_clipada, lista_campos_clipados). Não rejeita; só clipa.
    Ações marcadas como `rejected` ou `plausible=False` zeram tudo.
    """
    if not interp.plausible or interp.classification == "rejected":
        # Zera tudo defensivamente.
        return (
            GMInterpretation(
                classification="rejected",
                plausible=False,
                affected_metrics={},
                side_effects={},
                cost={},
                success_p=0.0,
                triggers_accident=False,
                narrative_seed=interp.narrative_seed,
                rejection_reason=interp.rejection_reason or "ação não plausível",
            ),
            [],
        )

    caps = CATEGORY_CAPS.get(interp.classification, CATEGORY_CAPS["research"])
    max_mag = float(caps["max_metric_delta"])
    max_n = int(caps["max_metrics_affected"])

    clipped_fields: List[str] = []

    def _clip_dict(d: Dict[str, float], label: str) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for k, v in d.items():
            if abs(v) > max_mag:
                clipped_fields.append(f"{label}.{k}")
                v = max_mag if v > 0 else -max_mag
            out[k] = float(v)
        return out

    affected = _clip_dict(dict(interp.affected_metrics), "affected_metrics")
    side = _clip_dict(dict(interp.side_effects), "side_effects")

    # Cap em número de métricas afetadas — keep top-N por |delta|
    if len(affected) > max_n:
        keep = sorted(affected.items(), key=lambda kv: -abs(kv[1]))[:max_n]
        dropped = set(affected) - {k for k, _ in keep}
        for k in dropped:
            clipped_fields.append(f"dropped.affected_metrics.{k}")
        affected = dict(keep)

    return (
        GMInterpretation(
            classification=interp.classification,
            plausible=True,
            affected_metrics=affected,
            side_effects=side,
            cost=dict(interp.cost),
            success_p=float(interp.success_p),
            triggers_accident=bool(interp.triggers_accident),
            narrative_seed=interp.narrative_seed,
            rejection_reason=None,
        ),
        clipped_fields,
    )


# ---------------------------------------------------------------------------- abstract GM


class GameMaster(ABC):
    """Interface do GM. Implementações: Gemini real, mock para testes."""

    @abstractmethod
    def interpret(
        self,
        prompt: str,
        *,
        year: float,
        turn: int,
        mission_name: str,
        mission_description: str,
        engine_state_summary: str,
        player_state: Dict[str, Any],
        recent_history: List[str],
    ) -> GMInterpretation:
        """Retorna interpretação estruturada da ação livre do jogador."""


# ---------------------------------------------------------------------------- Gemini-backed GM


def build_gm_function_declaration() -> dict:
    """Schema da função `interpret_action` que o GM-LLM deve chamar."""
    return {
        "name": "interpret_action",
        "description": (
            "Interpreta a ação proposta pelo jogador como Game Master de "
            "Counterfactual-1998. Retorna classificação, plausibilidade, "
            "métricas-mundo afetadas, side_effects, success_p e narrative_seed."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "classification": {
                    "type": "STRING",
                    "enum": [
                        "research", "deployment", "lobby", "partnership",
                        "comms", "m_and_a", "rejected",
                    ],
                    "description": "Categoria da ação proposta.",
                },
                "plausible": {
                    "type": "BOOLEAN",
                    "description": (
                        "True se a ação é viável no contexto histórico e "
                        "dado o estado atual do lab/mundo."
                    ),
                },
                "affected_metrics": {
                    "type": "OBJECT",
                    "description": (
                        "Dict metric_key -> delta (float). Use APENAS chaves "
                        "presentes em available_metrics. Magnitudes conservadoras."
                    ),
                },
                "side_effects": {
                    "type": "OBJECT",
                    "description": (
                        "Dict metric_key -> delta (float) com efeitos colaterais "
                        "PROPORCIONAIS à ação principal. Geralmente negativos."
                    ),
                },
                "cost": {
                    "type": "OBJECT",
                    "description": (
                        "Dict player_field -> delta. Campos: lab_funds, "
                        "reputation. Negativo gasta, positivo ganha."
                    ),
                },
                "success_p": {
                    "type": "NUMBER",
                    "description": (
                        "Probabilidade [0,1] de sucesso integral. Considere "
                        "contexto histórico e capacidade do lab."
                    ),
                },
                "triggers_accident": {
                    "type": "BOOLEAN",
                    "description": (
                        "True se a ação envolve risco real de acidente grave "
                        "(deploy rushed, experimento perigoso, etc). "
                        "Incrementa accidents_count do lab."
                    ),
                },
                "narrative_seed": {
                    "type": "STRING",
                    "description": (
                        "Frase de 15-30 palavras descrevendo o que acontece, "
                        "para o cronista usar como ponto de partida narrativo."
                    ),
                },
                "rejection_reason": {
                    "type": "STRING",
                    "nullable": True,
                    "description": (
                        "Se plausible=false, explique em 1-2 frases por quê. "
                        "Null caso contrário."
                    ),
                },
            },
            "required": [
                "classification", "plausible", "affected_metrics",
                "side_effects", "success_p", "narrative_seed",
            ],
        },
    }


def _read_gm_prompt() -> str:
    return GM_PROMPT_PATH.read_text(encoding="utf-8")


@dataclass
class GeminiGameMaster(GameMaster):
    """GM real, calls Gemini 2.5 Flash. Reusa cliente do cronista."""

    api_key: str
    model: str = GM_DEFAULT_MODEL
    temperature: float = GM_DEFAULT_TEMPERATURE
    log_path: Optional[Path] = None  # se setado, escreve gm_log.jsonl
    _client: Any = field(default=None, init=False)

    @classmethod
    def from_env(cls, **kwargs) -> "GeminiGameMaster":
        import os
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise PermanentError(
                "GEMINI_API_KEY/GOOGLE_API_KEY ausente; GM não pode falar com Gemini"
            )
        return cls(api_key=key, **kwargs)

    def _ensure_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def interpret(
        self,
        prompt: str,
        *,
        year: float,
        turn: int,
        mission_name: str,
        mission_description: str,
        engine_state_summary: str,
        player_state: Dict[str, Any],
        recent_history: List[str],
    ) -> GMInterpretation:
        """Interpreta a ação chamando Gemini com function calling estrito."""
        client = self._ensure_client()
        from google.genai import types

        available_metrics = list_available_metrics()
        category_caps_dump = json.dumps(CATEGORY_CAPS, ensure_ascii=False)

        gm_prompt_template = _read_gm_prompt()
        user_input = gm_prompt_template.format(
            year=f"{year:.1f}",
            turn=turn,
            mission_name=mission_name,
            mission_description=mission_description,
            state_summary=engine_state_summary,
            lab_funds=player_state.get("lab_funds", 0.0),
            accidents_count=player_state.get("accidents_count", 0),
            reputation=player_state.get("reputation", 0.0),
            accident_risk=player_state.get("accident_risk", 0.0),
            exposure_risk=player_state.get("exposure_risk", 0.0),
            alignment_credit=player_state.get("alignment_credit", 0.0),
            lab_lead_over_rivals=player_state.get("lab_lead_over_rivals", 0.0),
            recent_history="\n".join(f"- {h}" for h in recent_history[-3:]) or "(nenhum turno anterior)",
            player_prompt=prompt,
            available_metrics=", ".join(available_metrics),
            category_caps=category_caps_dump,
        )

        tool = types.Tool(function_declarations=[build_gm_function_declaration()])
        kwargs: Dict[str, Any] = dict(
            temperature=self.temperature,
            max_output_tokens=2048,
            tools=[tool],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY", allowed_function_names=["interpret_action"],
                )
            ),
            safety_settings=SAFETY_SETTINGS,
        )
        try:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        except (AttributeError, TypeError):
            pass

        t0 = time.time()
        try:
            response = client.models.generate_content(
                model=self.model,
                contents=user_input,
                config=types.GenerateContentConfig(**kwargs),
            )
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).lower()
            if "rate" in msg or "429" in msg or "quota" in msg or "timeout" in msg or "deadline" in msg:
                raise TransientError(str(exc)) from exc
            if "safety" in msg or "blocked" in msg:
                raise SafetyFilterError(str(exc)) from exc
            raise PermanentError(str(exc)) from exc

        elapsed = time.time() - t0
        args = _extract_function_call_args(response)
        if args is None:
            raise MalformedResponseError("GM: Gemini não chamou interpret_action")

        # Coage para schema. Pydantic permite missing optionals.
        try:
            interp = GMInterpretation(**args)
        except Exception as exc:  # noqa: BLE001
            raise MalformedResponseError(f"GM: schema inválido: {exc}") from exc

        # Logging estruturado
        if self.log_path is not None:
            self._log_call(
                turn=turn, prompt=prompt, raw=args, parsed=interp.model_dump(),
                latency=elapsed,
            )

        return interp

    def _log_call(
        self, *, turn: int, prompt: str, raw: dict, parsed: dict, latency: float,
    ) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "turn": turn,
                    "prompt": prompt,
                    "raw_response": raw,
                    "parsed": parsed,
                    "latency_seconds": latency,
                    "model": self.model,
                }, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("falha gravando gm_log: %s", exc)


# ---------------------------------------------------------------------------- helpers


def _extract_function_call_args(response: Any) -> Optional[Dict[str, Any]]:
    """Idem chronicler.gemini_client._extract_function_call_args."""
    candidates = getattr(response, "candidates", None) or []
    for cand in candidates:
        content = getattr(cand, "content", None)
        if not content:
            continue
        parts = getattr(content, "parts", None) or []
        for part in parts:
            fc = getattr(part, "function_call", None)
            if fc is not None:
                args = getattr(fc, "args", None)
                if args is not None:
                    return _to_plain_dict(args)
    return None


def _to_plain_dict(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _to_plain_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain_dict(v) for v in obj]
    if hasattr(obj, "items") and callable(obj.items):
        return {k: _to_plain_dict(v) for k, v in obj.items()}
    if hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
        try:
            return [_to_plain_dict(v) for v in obj]
        except TypeError:
            return obj
    return obj


# ---------------------------------------------------------------------------- mock GM


@dataclass
class StubGameMaster(GameMaster):
    """Mock GM determinístico — útil para testes e smoke offline.

    Sempre retorna a interpretação configurada em `fixed_interpretation`.
    Ou aceita um callable `interpret_fn(prompt, **kwargs) -> GMInterpretation`
    para mocks mais ricos.
    """

    fixed_interpretation: Optional[GMInterpretation] = None
    interpret_fn: Optional[Any] = None

    def interpret(self, prompt: str, **kwargs) -> GMInterpretation:
        if self.interpret_fn is not None:
            return self.interpret_fn(prompt, **kwargs)
        if self.fixed_interpretation is not None:
            return self.fixed_interpretation
        # Default: research moderado, success_p alto, sem accident
        return GMInterpretation(
            classification="research",
            plausible=True,
            affected_metrics={"ai_capability.frontier_capability.US": 0.5},
            side_effects={},
            cost={"lab_funds": -0.05},
            success_p=0.8,
            triggers_accident=False,
            narrative_seed="O lab investe em pesquisa interna sem grande visibilidade externa.",
        )
