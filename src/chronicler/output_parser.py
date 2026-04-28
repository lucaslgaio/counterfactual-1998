"""Validate and parse the chronicler's function-call response.

The chronicler is constrained by a function schema (see gemini_client) but
Gemini occasionally returns malformed responses. This module:

1. Asserts the structural fields exist.
2. Asserts narrative is in the expected word count range.
3. Asserts key_developments has 3-6 items.
4. Asserts confidence is one of the allowed strings.
5. Asserts event_outcome_explanation presence matches whether the engine
   sampled an event.

All violations raise ChroniclerOutputError so the retry layer can decide
to retry with lower temperature.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.chronicler.prompts import (
    KEY_DEVELOPMENTS_MAX,
    KEY_DEVELOPMENTS_MIN,
    NARRATIVE_MAX_WORDS,
    NARRATIVE_MIN_WORDS,
    VALID_CONFIDENCE,
)


class ChroniclerOutputError(ValueError):
    """Raised when the LLM response doesn't match the expected schema."""


@dataclass
class ChroniclerOutput:
    """Validated chronicler response for one turn."""

    narrative: str
    key_developments: List[str]
    event_outcome_explanation: Optional[str]
    confidence: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "narrative": self.narrative,
            "key_developments": list(self.key_developments),
            "event_outcome_explanation": self.event_outcome_explanation,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_json(cls, data: dict) -> "ChroniclerOutput":
        return cls(
            narrative=str(data["narrative"]),
            key_developments=list(data.get("key_developments", [])),
            event_outcome_explanation=data.get("event_outcome_explanation"),
            confidence=str(data.get("confidence", "medium")),
            metadata=dict(data.get("metadata", {})),
        )

    @property
    def word_count(self) -> int:
        return len(self.narrative.split())


def parse_chronicler_response(
    raw_response: dict,
    expected_event_outcome: bool,
    metadata: Optional[Dict[str, Any]] = None,
    strict_word_count: bool = False,
) -> ChroniclerOutput:
    """Parse a Gemini function_call ``args`` dict into a ChroniclerOutput.

    Args:
        raw_response: dict with keys ``narrative``, ``key_developments``,
            ``confidence``, optional ``event_outcome_explanation``.
        expected_event_outcome: True if the engine sampled an event this
            turn (so we expect a non-null explanation).
        metadata: optional extra fields (tokens used, latency).
        strict_word_count: if True, raise on word-count violations. If False,
            log them but return the output.

    Raises:
        ChroniclerOutputError on missing required fields or invalid enums.
    """
    if not isinstance(raw_response, dict):
        raise ChroniclerOutputError(
            f"expected dict response, got {type(raw_response).__name__}"
        )

    missing = [k for k in ("narrative", "key_developments", "confidence") if k not in raw_response]
    if missing:
        raise ChroniclerOutputError(f"missing required fields: {missing}")

    narrative = str(raw_response["narrative"]).strip()
    if not narrative:
        raise ChroniclerOutputError("narrative is empty")

    key_devs = raw_response.get("key_developments", [])
    if not isinstance(key_devs, list):
        raise ChroniclerOutputError(
            f"key_developments must be a list, got {type(key_devs).__name__}"
        )
    key_devs = [str(s).strip() for s in key_devs if str(s).strip()]
    if not (KEY_DEVELOPMENTS_MIN <= len(key_devs) <= KEY_DEVELOPMENTS_MAX):
        raise ChroniclerOutputError(
            f"key_developments must have {KEY_DEVELOPMENTS_MIN}-{KEY_DEVELOPMENTS_MAX} items, "
            f"got {len(key_devs)}"
        )

    confidence = str(raw_response["confidence"]).strip().lower()
    if confidence not in VALID_CONFIDENCE:
        raise ChroniclerOutputError(
            f"confidence must be one of {VALID_CONFIDENCE!r}, got {confidence!r}"
        )

    event_explanation = raw_response.get("event_outcome_explanation")
    if event_explanation == "":
        event_explanation = None
    if expected_event_outcome and not event_explanation:
        raise ChroniclerOutputError(
            "engine sampled an event this turn but chronicler did not provide "
            "event_outcome_explanation"
        )
    if not expected_event_outcome and event_explanation:
        # Soft warning; allow it but flag.
        # Some chroniclers may still want to comment on event-free turns.
        pass

    word_count = len(narrative.split())
    if strict_word_count and not (NARRATIVE_MIN_WORDS <= word_count <= NARRATIVE_MAX_WORDS):
        raise ChroniclerOutputError(
            f"narrative word count {word_count} outside [{NARRATIVE_MIN_WORDS}, {NARRATIVE_MAX_WORDS}]"
        )

    out_meta = dict(metadata or {})
    out_meta["word_count"] = word_count
    if not (NARRATIVE_MIN_WORDS <= word_count <= NARRATIVE_MAX_WORDS):
        out_meta["word_count_warning"] = True

    return ChroniclerOutput(
        narrative=narrative,
        key_developments=key_devs,
        event_outcome_explanation=event_explanation,
        confidence=confidence,
        metadata=out_meta,
    )
