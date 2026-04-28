"""Tests for src/chronicler/prompts.py."""
from src.chronicler.prompts import (
    CHRONICLER_SYSTEM_PROMPT,
    KEY_DEVELOPMENTS_MAX,
    KEY_DEVELOPMENTS_MIN,
    NARRATIVE_MAX_WORDS,
    NARRATIVE_MIN_WORDS,
    VALID_CONFIDENCE,
)


def test_system_prompt_nonempty():
    assert len(CHRONICLER_SYSTEM_PROMPT) > 1000
    assert "DIVISÃO DE TRABALHO" in CHRONICLER_SYSTEM_PROMPT


def test_system_prompt_has_no_decision_role():
    """The chronicler must not be told to decide what happens — that's the
    motor's job. The prompt should explicitly forbid it."""
    forbidden_phrasing = ("decida", "decida o que aconteceu", "calcule deltas")
    # Document that the prompt FORBIDS such activity
    assert "NÃO sugira causal_links" in CHRONICLER_SYSTEM_PROMPT
    assert "NÃO invente eventos" in CHRONICLER_SYSTEM_PROMPT
    assert "NÃO invente números" in CHRONICLER_SYSTEM_PROMPT


def test_system_prompt_word_count_constants():
    assert NARRATIVE_MIN_WORDS < NARRATIVE_MAX_WORDS
    assert NARRATIVE_MIN_WORDS == 150
    assert NARRATIVE_MAX_WORDS == 300


def test_key_developments_bounds():
    assert KEY_DEVELOPMENTS_MIN == 3
    assert KEY_DEVELOPMENTS_MAX == 6


def test_valid_confidence_strings():
    assert "low" in VALID_CONFIDENCE
    assert "medium" in VALID_CONFIDENCE
    assert "high" in VALID_CONFIDENCE
    assert len(VALID_CONFIDENCE) == 3
