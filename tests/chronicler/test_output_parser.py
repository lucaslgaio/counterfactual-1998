"""Tests for src/chronicler/output_parser.py."""
import pytest

from src.chronicler.output_parser import (
    ChroniclerOutput,
    ChroniclerOutputError,
    parse_chronicler_response,
)


def _good_response(narrative_words: int = 200, n_devs: int = 4) -> dict:
    """Build a synthetic valid response."""
    narrative = " ".join(["palavra"] * narrative_words)
    return {
        "narrative": narrative,
        "key_developments": [f"item {i}" for i in range(n_devs)],
        "event_outcome_explanation": None,
        "confidence": "medium",
    }


def test_parse_valid_response():
    out = parse_chronicler_response(_good_response(), expected_event_outcome=False)
    assert isinstance(out, ChroniclerOutput)
    assert out.confidence == "medium"
    assert len(out.key_developments) == 4


def test_parse_missing_field_raises():
    bad = _good_response()
    del bad["narrative"]
    with pytest.raises(ChroniclerOutputError, match="missing required fields"):
        parse_chronicler_response(bad, expected_event_outcome=False)


def test_parse_empty_narrative_raises():
    bad = _good_response()
    bad["narrative"] = ""
    with pytest.raises(ChroniclerOutputError, match="empty"):
        parse_chronicler_response(bad, expected_event_outcome=False)


def test_parse_too_few_key_developments_raises():
    bad = _good_response(n_devs=2)
    with pytest.raises(ChroniclerOutputError, match="key_developments"):
        parse_chronicler_response(bad, expected_event_outcome=False)


def test_parse_too_many_key_developments_raises():
    bad = _good_response(n_devs=10)
    with pytest.raises(ChroniclerOutputError, match="key_developments"):
        parse_chronicler_response(bad, expected_event_outcome=False)


def test_parse_invalid_confidence_raises():
    bad = _good_response()
    bad["confidence"] = "absolutely_certain"
    with pytest.raises(ChroniclerOutputError, match="confidence"):
        parse_chronicler_response(bad, expected_event_outcome=False)


def test_parse_event_explanation_required_when_event_sampled():
    bad = _good_response()
    bad["event_outcome_explanation"] = None
    with pytest.raises(ChroniclerOutputError, match="event_outcome_explanation"):
        parse_chronicler_response(bad, expected_event_outcome=True)


def test_parse_word_count_warning_metadata():
    """Out-of-range narrative word count is recorded but doesn't raise (default mode)."""
    bad = _good_response(narrative_words=50)
    out = parse_chronicler_response(bad, expected_event_outcome=False)
    assert out.metadata.get("word_count_warning") is True


def test_parse_strict_word_count_raises():
    bad = _good_response(narrative_words=50)
    with pytest.raises(ChroniclerOutputError, match="word count"):
        parse_chronicler_response(bad, expected_event_outcome=False, strict_word_count=True)


def test_chronicler_output_to_json_round_trip():
    out = ChroniclerOutput(
        narrative="some narrative " * 50,
        key_developments=["a", "b", "c"],
        event_outcome_explanation="ok",
        confidence="high",
        metadata={"latency": 1.0},
    )
    js = out.to_json()
    out2 = ChroniclerOutput.from_json(js)
    assert out2.narrative == out.narrative
    assert out2.confidence == out.confidence
    assert out2.metadata["latency"] == 1.0


def test_chronicler_output_word_count_property():
    out = ChroniclerOutput(
        narrative="one two three",
        key_developments=["a", "b", "c"],
        event_outcome_explanation=None,
        confidence="low",
    )
    assert out.word_count == 3


def test_parse_non_dict_raises():
    with pytest.raises(ChroniclerOutputError, match="dict"):
        parse_chronicler_response("not a dict", expected_event_outcome=False)  # type: ignore
