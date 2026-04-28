"""Wrapper around google.genai.Client tailored to the chronicler's contract.

Two responsibilities:
1. Build the ``chronicle_turn`` function declaration so Gemini returns
   structured output (no free-text drift).
2. Translate Gemini's response (or its error modes) into typed exceptions
   from ``retry.py`` so the retry layer can decide what to do.

Configuration choices match those validated empirically in the original
``src/llm.py``:
- thinking_budget=0 (CRITICAL — without this, max_output_tokens is consumed
  by reasoning before the function call lands)
- safety_settings=BLOCK_ONLY_HIGH on all 4 categories (historical content
  about wars, crises, etc. trips the default thresholds)
- function_calling mode="ANY", restricted to ``chronicle_turn``
- temperature default 0.85; lower (0.7) on retry after malformed output
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.chronicler.retry import (
    MalformedResponseError,
    PermanentError,
    SafetyFilterError,
    TransientError,
)

logger = logging.getLogger(__name__)

# Default model. Use Gemini 2.5 Flash for cost — chronicler doesn't need Pro.
DEFAULT_MODEL = "gemini-2.5-flash"

# Safety settings that allow historical content (wars, crises, conflict).
SAFETY_SETTINGS = [
    {"category": cat, "threshold": "BLOCK_ONLY_HIGH"}
    for cat in (
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
    )
]


def build_chronicler_function_declaration() -> dict:
    """Schema of the ``chronicle_turn`` function the LLM must call.

    Mirrors the ChroniclerOutput dataclass (output_parser.py).
    """
    return {
        "name": "chronicle_turn",
        "description": (
            "Narra em prosa o que o motor SDM calculou neste turno. NÃO sugira "
            "deltas, eventos ou causal_links — apenas interprete narrativamente."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "narrative": {
                    "type": "STRING",
                    "description": (
                        "Narrativa em português brasileiro, 150-300 palavras, "
                        "prosa contínua. Use a lente sociológica como ângulo "
                        "e as sementes como matéria-prima concreta."
                    ),
                },
                "key_developments": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "3 a 6 destaques curtos do semestre.",
                },
                "event_outcome_explanation": {
                    "type": "STRING",
                    "nullable": True,
                    "description": (
                        "Se o motor amostrou um evento âncora, prosa curta "
                        "explicando o porquê da variante saída (modulators e "
                        "estado-mundo). Null se nenhum evento foi amostrado."
                    ),
                },
                "confidence": {
                    "type": "STRING",
                    "enum": ["low", "medium", "high"],
                    "description": (
                        "Avaliação subjetiva sobre a coerência narrativa do "
                        "turno descrito."
                    ),
                },
            },
            "required": ["narrative", "key_developments", "confidence"],
        },
    }


# ---------------------------------------------------------------------------- client


@dataclass
class GeminiClient:
    """Thin wrapper around google.genai.Client.

    Public methods raise typed exceptions from retry.py — never bare
    Exception — so callers can compose retry policies cleanly.
    """

    api_key: str
    model: str = DEFAULT_MODEL
    _client: Any = field(default=None, init=False)

    @classmethod
    def from_env(cls, model: str = DEFAULT_MODEL) -> "GeminiClient":
        """Read GEMINI_API_KEY (or GOOGLE_API_KEY as fallback) from env."""
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise PermanentError(
                "neither GEMINI_API_KEY nor GOOGLE_API_KEY found in environment; "
                "the chronicler can't talk to Gemini without one"
            )
        return cls(api_key=key, model=model)

    def _ensure_client(self):
        if self._client is None:
            from google import genai  # local import keeps test files importable
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def call_chronicler(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.85,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Make one call. Returns the function_call args dict on success.

        Raises:
            TransientError: rate limit / timeout / network error.
            MalformedResponseError: response present but no function_call args.
            SafetyFilterError: response blocked by safety filter.
            PermanentError: auth, schema, or other non-retryable issue.
        """
        client = self._ensure_client()
        try:
            from google.genai import types  # noqa: WPS433
        except ImportError as exc:
            raise PermanentError(f"google.genai not installed: {exc}") from exc

        tool = types.Tool(function_declarations=[build_chronicler_function_declaration()])
        kwargs: Dict[str, Any] = dict(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            tools=[tool],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY",
                    allowed_function_names=["chronicle_turn"],
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
            if "rate" in msg or "429" in msg or "quota" in msg:
                raise TransientError(str(exc)) from exc
            if "timeout" in msg or "deadline" in msg:
                raise TransientError(str(exc)) from exc
            if "safety" in msg or "blocked" in msg:
                raise SafetyFilterError(str(exc)) from exc
            raise PermanentError(str(exc)) from exc

        elapsed = time.time() - t0

        # Extract function_call args
        args = _extract_function_call_args(response)
        if args is None:
            details = _diagnostic_details(response)
            raise MalformedResponseError(
                "Gemini returned no function_call. Diagnostics:\n" + "\n".join(details)
            )

        # Attach metadata
        usage = getattr(response, "usage_metadata", None)
        meta = {
            "latency_seconds": elapsed,
            "model": self.model,
            "temperature": temperature,
        }
        if usage:
            meta["prompt_tokens"] = getattr(usage, "prompt_token_count", None)
            meta["completion_tokens"] = getattr(usage, "candidates_token_count", None)
            meta["total_tokens"] = getattr(usage, "total_token_count", None)
        args["_metadata"] = meta
        return args


# ---------------------------------------------------------------------------- helpers


def _extract_function_call_args(response: Any) -> Optional[Dict[str, Any]]:
    """Walk the response candidates and pull the first function_call.args dict."""
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
    """Recursively convert proto MapComposite / RepeatedComposite to plain Python."""
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


def _diagnostic_details(response: Any) -> List[str]:
    """Pretty-print diagnostic info when no function_call was returned."""
    details = []
    candidates = getattr(response, "candidates", None) or []
    for i, cand in enumerate(candidates):
        details.append(f"  candidate[{i}].finish_reason: {getattr(cand, 'finish_reason', '?')}")
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if not parts:
            details.append(f"  candidate[{i}]: no content.parts")
            continue
        for j, part in enumerate(parts):
            text = getattr(part, "text", None)
            if text:
                snippet = text[:300] + ("..." if len(text) > 300 else "")
                details.append(f"  candidate[{i}].part[{j}].text: {snippet!r}")
    usage = getattr(response, "usage_metadata", None)
    if usage:
        details.append(
            f"  usage: prompt={getattr(usage, 'prompt_token_count', '?')} "
            f"completion={getattr(usage, 'candidates_token_count', '?')} "
            f"total={getattr(usage, 'total_token_count', '?')}"
        )
    return details
