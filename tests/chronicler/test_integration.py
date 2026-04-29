"""Integration tests for the chronicler with the real Gemini API.

These are SKIPPED by default — they require GEMINI_API_KEY (or GOOGLE_API_KEY)
in the environment AND make real network calls (cost ~$0.01 per turn).

Run manually with:

    pytest tests/chronicler/test_integration.py -v -m integration

Or include integration in the default run:

    pytest tests/ -v --run-integration
"""
from __future__ import annotations

import os

import pytest

from src.chronicler.chronicler import ChroniclerSession
from src.chronicler.gemini_client import GeminiClient
from src.engine.simulation import Simulation


pytestmark = pytest.mark.skipif(
    not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
    reason="No GEMINI_API_KEY/GOOGLE_API_KEY in environment — integration test skipped",
)


@pytest.mark.integration
def test_chronicle_one_real_turn():
    """End-to-end smoke test: run engine for one turn, chronicle it via Gemini."""
    sim = Simulation.from_spec(seed=42)
    initial = sim.state
    result = sim.run_turn()

    client = GeminiClient.from_env()
    session = ChroniclerSession(client=client, seed=42)
    out = session.chronicle_turn(result, initial, result.state_after)

    assert out.narrative
    assert 100 <= len(out.narrative.split()) <= 400, (
        f"narrative word count {len(out.narrative.split())} unreasonable"
    )
    assert 3 <= len(out.key_developments) <= 6
    assert out.confidence in ("low", "medium", "high")
    print("\n--- Chronicled turn 1 ---")
    print(out.narrative)
    print("\nKey developments:", out.key_developments)
    print("Confidence:", out.confidence)


@pytest.mark.integration
def test_chronicle_three_real_turns_for_coherence():
    """Three consecutive turns should produce a coherent micro-story."""
    sim = Simulation.from_spec(seed=42)
    results = sim.run_many(3)
    states = [results[0].state_before] + [r.state_after for r in results]

    client = GeminiClient.from_env()
    session = ChroniclerSession(client=client, seed=42)
    chronicled = session.chronicle_run(results, states)

    assert len(chronicled) == 3
    print("\n--- Chronicled turns 1-3 ---")
    for i, c in enumerate(chronicled):
        print(f"\nTurn {i+1} ({results[i].turn_label}):")
        print(c.narrative)
