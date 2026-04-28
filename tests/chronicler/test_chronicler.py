"""Tests for src/chronicler/chronicler.py — uses a mock GeminiClient."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from src.chronicler.chronicler import ChroniclerSession
from src.chronicler.gemini_client import GeminiClient
from src.chronicler.output_parser import ChroniclerOutput
from src.chronicler.retry import MalformedResponseError, RetryConfig, SafetyFilterError
from src.engine.simulation import Simulation


def _make_good_response(narrative_words: int = 200, n_devs: int = 4, with_event: bool = False) -> Dict[str, Any]:
    return {
        "narrative": " ".join(["palavra"] * narrative_words),
        "key_developments": [f"item {i}" for i in range(n_devs)],
        "event_outcome_explanation": "evento explicado" if with_event else None,
        "confidence": "medium",
        "_metadata": {"latency_seconds": 1.0, "model": "mock"},
    }


def _make_smart_mock(default_response_factory):
    """Build a side_effect that always returns a response shape matching whether
    the caller's user_input mentions a sampled event.

    Inspects the user_input string for the absence of "Nenhum evento" and
    returns event_outcome_explanation accordingly.
    """

    def side_effect(*args, **kwargs):
        user_input = kwargs.get("user_input") or (args[1] if len(args) > 1 else "")
        has_event = "Nenhum evento" not in user_input
        return default_response_factory(with_event=has_event)

    return side_effect


def _make_bad_response() -> Dict[str, Any]:
    """Missing required fields."""
    return {"_metadata": {}, "narrative": ""}  # empty narrative triggers parser error


def _make_mock_client(response_or_func) -> GeminiClient:
    """Builds a GeminiClient whose call_chronicler is mocked."""
    client = GeminiClient(api_key="mock-key", model="mock")
    if callable(response_or_func):
        client.call_chronicler = MagicMock(side_effect=response_or_func)
    else:
        client.call_chronicler = MagicMock(return_value=response_or_func)
    return client


def _one_turn_artifacts():
    sim = Simulation.from_spec(seed=42)
    initial = sim.state
    result = sim.run_turn()
    return result, initial, result.state_after


def test_chronicle_turn_returns_output_on_good_response():
    client = _make_mock_client(lambda **kw: _make_good_response())
    session = ChroniclerSession(client=client, seed=42)
    result, before, after = _one_turn_artifacts()
    out = session.chronicle_turn(result, before, after)
    assert isinstance(out, ChroniclerOutput)
    assert out.confidence == "medium"
    # client called exactly once
    assert client.call_chronicler.call_count == 1
    # narrative recorded in history
    assert len(session.narrative_history) == 1


def test_chronicle_turn_retries_on_malformed_then_succeeds():
    """First attempt malformed → second attempt good."""
    counter = {"n": 0}

    def side_effect(**kw):
        counter["n"] += 1
        if counter["n"] == 1:
            return _make_bad_response()
        return _make_good_response()

    client = _make_mock_client(side_effect)
    session = ChroniclerSession(
        client=client,
        seed=42,
        retry_config=RetryConfig(max_retries=2, initial_backoff_seconds=0.001),
    )
    result, before, after = _one_turn_artifacts()
    out = session.chronicle_turn(result, before, after)
    assert isinstance(out, ChroniclerOutput)
    assert client.call_chronicler.call_count == 2


def test_chronicle_turn_eventually_raises_after_persistent_malformed():
    client = _make_mock_client(lambda **kw: _make_bad_response())
    session = ChroniclerSession(
        client=client,
        seed=42,
        retry_config=RetryConfig(max_retries=2, initial_backoff_seconds=0.001),
    )
    result, before, after = _one_turn_artifacts()
    with pytest.raises(MalformedResponseError):
        session.chronicle_turn(result, before, after)


def test_chronicle_turn_safety_filter_propagates():
    def side_effect(**kw):
        raise SafetyFilterError("blocked")

    client = _make_mock_client(side_effect)
    session = ChroniclerSession(
        client=client,
        seed=42,
        retry_config=RetryConfig(max_retries=2, initial_backoff_seconds=0.001),
    )
    result, before, after = _one_turn_artifacts()
    with pytest.raises(SafetyFilterError):
        session.chronicle_turn(result, before, after)
    # Safety filter is not retried.
    assert client.call_chronicler.call_count == 1


def test_chronicle_run_iterates_through_all_turns():
    sim = Simulation.from_spec(seed=42)
    results = sim.run_many(3)
    states = [results[0].state_before] + [r.state_after for r in results]

    client = _make_mock_client(_make_smart_mock(_make_good_response))
    session = ChroniclerSession(client=client, seed=42)
    chronicled = session.chronicle_run(results, states)
    assert len(chronicled) == len(results)
    assert client.call_chronicler.call_count == len(results)


def test_chronicle_run_validates_states_length():
    sim = Simulation.from_spec(seed=42)
    results = sim.run_many(3)
    states = [results[0].state_before]  # too short
    client = _make_mock_client(lambda **kw: _make_good_response())
    session = ChroniclerSession(client=client, seed=42)
    with pytest.raises(ValueError, match="states must have"):
        session.chronicle_run(results, states)


def test_chronicler_session_uses_lens_and_seeds_metadata():
    """The chronicler should inject lens and seed count into output metadata."""
    client = _make_mock_client(lambda **kw: _make_good_response())
    session = ChroniclerSession(client=client, seed=42)
    result, before, after = _one_turn_artifacts()
    out = session.chronicle_turn(result, before, after)
    assert "lens" in out.metadata
    assert "seeds_count" in out.metadata


def test_chronicler_session_history_grows_per_turn():
    sim = Simulation.from_spec(seed=42)
    results = sim.run_many(5)
    states = [results[0].state_before] + [r.state_after for r in results]
    client = _make_mock_client(_make_smart_mock(_make_good_response))
    session = ChroniclerSession(client=client, seed=42)
    session.chronicle_run(results, states)
    assert len(session.narrative_history) == len(results)
