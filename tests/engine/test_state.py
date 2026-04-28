"""Tests for src/engine/state.py."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.engine.state import (
    BLOCKS,
    TURN_LABELS,
    WorldState,
    _split_block_suffix,
)


def test_turn_labels_count_and_format():
    assert len(TURN_LABELS) == 58
    assert TURN_LABELS[0] == "1998-S1"
    assert TURN_LABELS[-1] == "2026-S2"
    assert TURN_LABELS[1] == "1998-S2"
    assert TURN_LABELS[2] == "1999-S1"


def test_from_initial_spec_loads_baseline():
    state = WorldState.from_initial_spec()
    assert state.turn_index == 0
    assert state.turn_label == "1998-S1"
    # 10 global metrics
    assert len(state.global_metrics) == 10
    # 14 vectorized metrics × 4 blocks
    assert len(state.block_metrics) == 14
    for key, sub in state.block_metrics.items():
        assert set(sub.keys()) == set(BLOCKS), f"{key} blocks: {sub.keys()}"
    # 2 matrix metrics
    assert len(state.matrix_metrics) == 2


def test_initial_spec_known_anchors():
    state = WorldState.from_initial_spec()
    assert state.block_metrics["ai_capability.frontier_capability"]["US"] == 92
    assert state.block_metrics["ai_capability.frontier_capability"]["CN"] == 35
    assert state.global_metrics["financial_markets.global_index"] == 100
    assert state.global_metrics["energy_climate.co2_gt_year"] == 24.4


def test_immutability():
    state = WorldState.from_initial_spec()
    with pytest.raises(FrozenInstanceError):
        state.turn_index = 5  # type: ignore[misc]


def test_with_advanced_turn():
    s0 = WorldState.from_initial_spec()
    s1 = s0.with_advanced_turn()
    assert s1.turn_index == 1
    assert s1.turn_label == "1998-S2"
    # original untouched
    assert s0.turn_index == 0
    assert s0.turn_label == "1998-S1"


def test_with_metadata_returns_new_object():
    s0 = WorldState.from_initial_spec()
    s1 = s0.with_metadata(seed=42, run_id="abc")
    assert s1.metadata["seed"] == 42
    assert "seed" not in s0.metadata


def test_json_round_trip():
    s = WorldState.from_initial_spec()
    js = s.to_json()
    s2 = WorldState.from_json(js)
    assert s2.turn_index == s.turn_index
    assert s2.turn_label == s.turn_label
    assert s2.global_metrics == s.global_metrics
    assert s2.block_metrics == s.block_metrics
    assert s2.matrix_metrics == s.matrix_metrics


def test_split_block_suffix():
    assert _split_block_suffix("ai_capability.frontier_capability") == (
        "ai_capability.frontier_capability",
        None,
    )
    assert _split_block_suffix("ai_capability.frontier_capability.US") == (
        "ai_capability.frontier_capability",
        "US",
    )
    assert _split_block_suffix("geopolitics.bilateral_tensions.US_CN") == (
        "geopolitics.bilateral_tensions",
        "US_CN",
    )


def test_get_metric_global():
    s = WorldState.from_initial_spec()
    assert s.get_metric("financial_markets.global_index") == 100


def test_get_metric_vectorized_with_block():
    s = WorldState.from_initial_spec()
    assert s.get_metric("ai_capability.frontier_capability.US") == 92


def test_get_metric_vectorized_without_block_raises():
    s = WorldState.from_initial_spec()
    with pytest.raises(ValueError, match="without block suffix"):
        s.get_metric("ai_capability.frontier_capability")


def test_get_metric_unknown_returns_nan():
    s = WorldState.from_initial_spec()
    import math

    assert math.isnan(s.get_metric("nonexistent.metric"))
