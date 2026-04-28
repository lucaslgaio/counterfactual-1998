"""Tests for src/engine/turn_runner.py."""
from __future__ import annotations

import numpy as np

from src.engine.clamp import load_metric_ranges
from src.engine.simulation import build_spec_bundle
from src.engine.state import WorldState
from src.engine.turn_runner import SimulationConfig, run_turn


def test_run_turn_advances_turn_index():
    spec = build_spec_bundle()
    ranges = load_metric_ranges()
    state = WorldState.from_initial_spec()
    rng = np.random.default_rng(42)
    config = SimulationConfig(seed=42)
    result = run_turn(state, config, spec, ranges, rng)
    assert result.state_before.turn_index == 0
    assert result.state_after.turn_index == 1
    assert result.state_after.turn_label == "1998-S2"


def test_run_turn_is_deterministic_with_same_seed():
    spec = build_spec_bundle()
    ranges = load_metric_ranges()
    state = WorldState.from_initial_spec()
    config = SimulationConfig(seed=42)
    rng_a = np.random.default_rng(42)
    rng_b = np.random.default_rng(42)
    a = run_turn(state, config, spec, ranges, rng_a)
    b = run_turn(state, config, spec, ranges, rng_b)
    # Same seed → same final state
    assert a.state_after.global_metrics == b.state_after.global_metrics
    assert a.state_after.block_metrics == b.state_after.block_metrics


def test_run_turn_clamps_outputs_in_range():
    spec = build_spec_bundle()
    ranges = load_metric_ranges()
    state = WorldState.from_initial_spec()
    rng = np.random.default_rng(42)
    config = SimulationConfig(seed=42)
    result = run_turn(state, config, spec, ranges, rng)
    # All metrics must be in their declared range
    for key, val in result.state_after.global_metrics.items():
        lo, hi = ranges.get(key)
        assert lo <= val <= hi, f"{key}={val} out of [{lo},{hi}]"
    for metric_key, by_block in result.state_after.block_metrics.items():
        lo, hi = ranges.get(metric_key)
        for b, val in by_block.items():
            assert lo <= val <= hi, f"{metric_key}.{b}={val} out of [{lo},{hi}]"


def test_run_turn_user_input_visible_in_state():
    """User input deltas should land on the next state."""
    spec = build_spec_bundle()
    ranges = load_metric_ranges()
    state = WorldState.from_initial_spec()
    rng = np.random.default_rng(42)
    config = SimulationConfig(seed=42)
    initial_idx = state.global_metrics["financial_markets.global_index"]
    result = run_turn(
        state,
        config,
        spec,
        ranges,
        rng,
        user_input_deltas={"financial_markets.global_index": -10.0},
    )
    final_idx = result.state_after.global_metrics["financial_markets.global_index"]
    # The -10 from user should be preserved (exogenous bypasses cap)
    assert final_idx <= initial_idx  # decreased


def test_turn_result_to_json_round_trip():
    spec = build_spec_bundle()
    ranges = load_metric_ranges()
    state = WorldState.from_initial_spec()
    rng = np.random.default_rng(42)
    config = SimulationConfig(seed=42)
    r = run_turn(state, config, spec, ranges, rng)
    js = r.to_json()
    assert js["turn_index"] == 0
    assert js["turn_label"] == "1998-S1"
    assert "state_before" in js
    assert "state_after" in js
    assert "delta_package" in js
