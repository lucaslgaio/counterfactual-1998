"""Cliente Google Gemini com function calling forçado para garantir saída estruturada."""
from __future__ import annotations

import os
from typing import Any, Optional

from google import genai
from google.genai import types

from src.config import SimulationConfig
from src.models import (
    ExogenousShock,
    HistoricalEvent,
    State,
    TurnResponse,
    list_metric_keys,
)
from src.prompts import SYSTEM_PROMPT, build_user_message


def _build_function_declaration() -> dict:
    """Schema da função `advance_turn` em formato Gemini (JSON Schema com tipos uppercase).

    Os deltas são passados como ARRAY de {metric, value} em vez de OBJECT
    com 24 propriedades nomeadas — Gemini engasga em MALFORMED_FUNCTION_CALL
    quando o schema tem property names com pontos (ex: 'ai_capability.frontier_capability').
    """
    valid_metrics_str = ", ".join(list_metric_keys())

    return {
        "name": "advance_turn",
        "description": (
            "Avança a simulação em um semestre. Retorna narrativa, deltas aplicados, "
            "links causais que explicam os deltas, e metadados sobre o evento histórico."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "narrative": {
                    "type": "STRING",
                    "description": "Narrativa em português brasileiro, 80-200 palavras.",
                },
                "key_developments": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "2 a 4 highlights curtos do semestre.",
                },
                "event_outcome": {
                    "type": "STRING",
                    "enum": ["ocorreu", "alterado", "anulado", "N/A"],
                    "description": "Como o evento histórico real evoluiu. N/A se não havia evento.",
                },
                "event_outcome_explanation": {
                    "type": "STRING",
                    "nullable": True,
                    "description": "Justificativa quando o outcome não foi 'ocorreu' ou 'N/A'.",
                },
                "deltas": {
                    "type": "ARRAY",
                    "description": (
                        "Lista de deltas aditivos. Inclua apenas métricas que mudaram. "
                        f"O campo 'metric' deve ser exatamente uma destas: {valid_metrics_str}."
                    ),
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "metric": {
                                "type": "STRING",
                                "description": "Métrica afetada, formato 'dimensao.metrica'.",
                            },
                            "value": {
                                "type": "NUMBER",
                                "description": "Delta aditivo (positivo ou negativo).",
                            },
                        },
                        "required": ["metric", "value"],
                    },
                },
                "causal_links": {
                    "type": "ARRAY",
                    "description": (
                        "3 a 8 conexões causais que justificam os deltas deste turno. "
                        "Cada link aponta de uma origem (evento, choque ou métrica) "
                        "para uma métrica afetada."
                    ),
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "source": {
                                "type": "STRING",
                                "description": (
                                    "Origem: nome curto do evento/choque, ou 'dimensao.metrica'. "
                                    "Ex: 'crise_russa', 'projeto_athena', "
                                    "'ai_capability.frontier_capability'."
                                ),
                            },
                            "target": {
                                "type": "STRING",
                                "description": "Métrica afetada, formato 'dimensao.metrica'.",
                            },
                            "direction": {
                                "type": "STRING",
                                "enum": ["up", "down"],
                            },
                        },
                        "required": ["source", "target", "direction"],
                    },
                },
                "confidence": {
                    "type": "STRING",
                    "enum": ["low", "medium", "high"],
                    "description": "Confiança do motor neste turno.",
                },
            },
            "required": [
                "narrative",
                "key_developments",
                "event_outcome",
                "deltas",
                "causal_links",
                "confidence",
            ],
        },
    }


# Conteúdo histórico da simulação (guerras, crises, etc) é tratado como
# legítimo — relaxamos os filtros do Gemini sem desligá-los completamente.
_SAFETY_SETTINGS = [
    {"category": cat, "threshold": "BLOCK_ONLY_HIGH"}
    for cat in (
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
    )
]


def get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY não está definida no ambiente. "
            "Pegue uma key gratuita em https://aistudio.google.com e cole no .env."
        )
    return genai.Client(api_key=api_key)


def _to_plain_dict(obj: Any) -> Any:
    """Converte recursivamente estruturas dict-like (proto.MapComposite) em dicts/listas puros."""
    if isinstance(obj, dict):
        return {k: _to_plain_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain_dict(v) for v in obj]
    if hasattr(obj, "items") and callable(obj.items):
        return {k: _to_plain_dict(v) for k, v in obj.items()}
    return obj


def simulate_turn(
    client: genai.Client,
    state: State,
    event: Optional[HistoricalEvent],
    shock: Optional[ExogenousShock],
    user_input: Optional[str],
    narrative_history: list,
    config: SimulationConfig,
) -> TurnResponse:
    """Executa um turno: chama o Gemini com function calling forçado, retorna TurnResponse validada."""
    user_message = build_user_message(
        state=state,
        event=event,
        shock=shock,
        user_input=user_input,
        narrative_history=narrative_history,
        config=config,
    )

    tool = types.Tool(function_declarations=[_build_function_declaration()])

    # Modelos 2.5+ têm "thinking" ligado por default, que consome tokens do
    # max_output_tokens antes de chegar na function call. Desligamos pra
    # não cair em MALFORMED_FUNCTION_CALL por truncamento.
    generate_config_kwargs: dict[str, Any] = dict(
        system_instruction=SYSTEM_PROMPT,
        temperature=config.temperature,
        max_output_tokens=config.max_tokens,
        tools=[tool],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=["advance_turn"],
            )
        ),
        safety_settings=_SAFETY_SETTINGS,
    )
    try:
        generate_config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    except (AttributeError, TypeError):
        # SDK antiga sem ThinkingConfig — ignora.
        pass

    response = client.models.generate_content(
        model=config.model,
        contents=user_message,
        config=types.GenerateContentConfig(**generate_config_kwargs),
    )

    # Extrai a primeira function_call do candidato
    function_call = None
    for candidate in response.candidates or []:
        if not candidate.content or not candidate.content.parts:
            continue
        for part in candidate.content.parts:
            if part.function_call is not None:
                function_call = part.function_call
                break
        if function_call:
            break

    if function_call is None:
        # Diagnóstico detalhado pra debug — mostra o que o modelo realmente retornou.
        details = []
        for i, candidate in enumerate(response.candidates or []):
            details.append(f"  candidate[{i}].finish_reason: {candidate.finish_reason}")
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) if content else None
            if not parts:
                details.append(f"  candidate[{i}]: sem content.parts")
                continue
            for j, part in enumerate(parts):
                text = getattr(part, "text", None)
                fc = getattr(part, "function_call", None)
                if text:
                    snippet = text if len(text) < 400 else (text[:400] + "...[truncado]")
                    details.append(f"  candidate[{i}].part[{j}].text: {snippet!r}")
                if fc is not None:
                    details.append(f"  candidate[{i}].part[{j}].function_call: name={fc.name!r}")
        usage = getattr(response, "usage_metadata", None)
        if usage:
            details.append(
                f"  usage: prompt={getattr(usage, 'prompt_token_count', '?')}, "
                f"total={getattr(usage, 'total_token_count', '?')}, "
                f"candidates={getattr(usage, 'candidates_token_count', '?')}, "
                f"thoughts={getattr(usage, 'thoughts_token_count', '?')}"
            )
        raise RuntimeError("Gemini não retornou function_call.\n" + "\n".join(details))

    args = _to_plain_dict(function_call.args)
    return TurnResponse.model_validate(args)
