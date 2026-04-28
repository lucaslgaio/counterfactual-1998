"""Tests for src/engine/clamp.py."""
from __future__ import annotations

from src.engine.clamp import clamp_state, load_metric_ranges
from src.engine.state import WorldState


def test_load_metric_ranges():
    ranges = load_metric_ranges()
    # Check known anchors
    assert ranges.get("ai_capability.frontier_capability") == (0.0, 100.0)
    assert ranges.get("inequality.gini_intra_block") == (0.0, 1.0)
    assert ranges.get("health.life_expectancy") == (0.0, 120.0)
    # Unknown metric returns infinite range
    lo, hi = ranges.get("nonexistent")
    assert lo == float("-inf") and hi == float("inf")


def test_clamp_state_caps_at_max():
    ranges = load_metric_ranges()
    s = WorldState.from_initial_spec()
    # Manually create a state with out-of-range values
    bad = WorldState(
        turn_index=s.turn_index,
        turn_label=s.turn_label,
        global_metrics={"financial_markets.global_index": 99999},  # exceeds 10000
        block_metrics={
            "ai_capability.frontier_capability": {"US": 200, "EU": 78, "CN": 35, "RoW": 18}
        },
        matrix_metrics={},
        metadata={},
    )
    clamped = clamp_state(bad, ranges)
    assert clamped.global_metrics["financial_markets.global_index"] == 10000
    assert clamped.block_metrics["ai_capability.frontier_capability"]["US"] == 100


def test_clamp_state_floors_at_min():
    ranges = load_metric_ranges()
    bad = WorldState(
        turn_index=0,
        turn_label="1998-S1",
        global_metrics={"inequality.top1pct_share": -5.0},  # below 0
        block_metrics={"inequality.gini_intra_block": {"US": -0.1, "EU": 0.3, "CN": 0.4, "RoW": 0.48}},
        matrix_metrics={},
        metadata={},
    )
    clamped = clamp_state(bad, ranges)
    assert clamped.global_metrics["inequality.top1pct_share"] == 0
    assert clamped.block_metrics["inequality.gini_intra_block"]["US"] == 0


def test_clamp_state_preserves_in_range_values():
    ranges = load_metric_ranges()
    s = WorldState.from_initial_spec()
    clamped = clamp_state(s, ranges)
    assert clamped.global_metrics == s.global_metrics
    assert clamped.block_metrics == s.block_metrics
    assert clamped.matrix_metrics == s.matrix_metrics


def test_clamp_state_returns_new_object():
    ranges = load_metric_ranges()
    s = WorldState.from_initial_spec()
    clamped = clamp_state(s, ranges)
    assert clamped is not s
