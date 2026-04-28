"""Tests for src/engine/event_sampler.py."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from src.engine.event_sampler import (
    evaluate_composite_factor,
    find_event_for_turn,
    sample_event,
)
from src.engine.state import WorldState
from src.spec.events import CompositeFactor, load_events

SPEC_DIR = Path(__file__).parent.parent.parent / "spec"


def _events():
    return load_events(SPEC_DIR / "event_variants.json")


def test_find_event_for_turn_found():
    spec = _events()
    ev = find_event_for_turn("1998-S2", spec)
    assert ev is not None
    assert ev.event_id.startswith("1998-S2")


def test_find_event_for_turn_missing_returns_none():
    spec = _events()
    # 1998-S1 has no anchor event in this spec
    assert find_event_for_turn("1998-S1", spec) is None


def test_evaluate_composite_factor_simple():
    cf = CompositeFactor(
        id="test",
        formula="0.5 * ai_capability.frontier_capability.US",
        normalization="divide_by_100",
    )
    state = WorldState.from_initial_spec()
    # US frontier = 92, coefficient 0.5 → 46, normalized → 0.46
    v = evaluate_composite_factor(cf, state)
    assert abs(v - 0.46) < 1e-6


def test_evaluate_composite_factor_negative_term():
    cf = CompositeFactor(
        id="test",
        formula="0.5 * ai_capability.frontier_capability.US - 0.2 * ai_capability.frontier_capability.CN",
        normalization="divide_by_100",
    )
    state = WorldState.from_initial_spec()
    # 0.5 * 92 - 0.2 * 35 = 46 - 7 = 39 → /100 = 0.39
    v = evaluate_composite_factor(cf, state)
    assert abs(v - 0.39) < 1e-6


def test_sample_event_returns_none_when_no_anchor():
    state = WorldState.from_initial_spec()
    rng = np.random.default_rng(42)
    spec = _events()
    # 1998-S1 has no anchor → None
    assert sample_event("1998-S1", state, rng, spec) is None


def test_sample_event_returns_one_of_the_variants():
    state = WorldState.from_initial_spec()
    rng = np.random.default_rng(42)
    spec = _events()
    ev = sample_event("1998-S2", state, rng, spec)
    assert ev is not None
    assert ev.event_id.startswith("1998-S2")
    # One of the documented variants
    valid_ids = {"real", "mitigado", "evitado"}
    assert ev.variant_id in valid_ids


def test_sample_event_is_deterministic_with_same_seed():
    state = WorldState.from_initial_spec()
    spec = _events()
    rng_a = np.random.default_rng(42)
    rng_b = np.random.default_rng(42)
    ev_a = sample_event("1998-S2", state, rng_a, spec)
    ev_b = sample_event("1998-S2", state, rng_b, spec)
    assert ev_a.variant_id == ev_b.variant_id


def test_sample_event_distribution_over_many_seeds():
    """With base probs ~0.6/0.3/0.1 (russa event) and small modulators (US
    frontier=92 → composite ai_intelligence_composite_US is meaningful but
    bounded), the dominant variant should still win majority of seeds."""
    state = WorldState.from_initial_spec()
    spec = _events()
    counts = {"real": 0, "mitigado": 0, "evitado": 0}
    for seed in range(200):
        ev = sample_event("1998-S2", state, np.random.default_rng(seed), spec)
        counts[ev.variant_id] += 1
    # Modulators may shift the distribution from base 0.6/0.3/0.1, but no
    # variant should disappear in 200 trials.
    for name, c in counts.items():
        assert c > 0, f"variant {name} never sampled in 200 trials: {counts}"
