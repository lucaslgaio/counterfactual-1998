"""Tests for src/engine/aggregation.py."""
from __future__ import annotations

import pytest

from src.engine.aggregation import (
    DEFAULT_GDP_WEIGHTS_1998,
    VALID_RULES,
    aggregate,
)


def test_default_weights_sum_to_one():
    assert abs(sum(DEFAULT_GDP_WEIGHTS_1998.values()) - 1.0) < 1e-9


def test_leader_picks_max():
    bv = {"US": 92, "EU": 78, "CN": 35, "RoW": 18}
    assert aggregate(bv, "leader") == 92


def test_max_picks_max():
    bv = {"US": 5, "EU": 12, "CN": 3, "RoW": 1}
    assert aggregate(bv, "max") == 12


def test_sum_adds_all():
    bv = {"US": 10, "EU": 20, "CN": 30, "RoW": 40}
    assert aggregate(bv, "sum") == 100


def test_weighted_mean_default_weights():
    # All blocks at value 50 → mean is 50 regardless of weights
    bv = {"US": 50, "EU": 50, "CN": 50, "RoW": 50}
    assert abs(aggregate(bv, "weighted_mean") - 50.0) < 1e-9


def test_weighted_mean_us_dominates_with_high_weight():
    bv = {"US": 100, "EU": 0, "CN": 0, "RoW": 0}
    # GDP weight US=0.30, total=1.0 → weighted=30
    assert abs(aggregate(bv, "weighted_mean") - 30.0) < 1e-9


def test_weighted_mean_with_override_weights():
    bv = {"US": 50, "EU": 50, "CN": 50, "RoW": 50}
    # Override: US gets all weight → result = US value = 50
    weights = {"US": 1.0, "EU": 0.0, "CN": 0.0, "RoW": 0.0}
    assert abs(aggregate(bv, "weighted_mean", weights) - 50.0) < 1e-9


def test_all_zeros_returns_zero_not_nan():
    bv = {"US": 0, "EU": 0, "CN": 0, "RoW": 0}
    assert aggregate(bv, "leader") == 0.0
    assert aggregate(bv, "weighted_mean") == 0.0
    assert aggregate(bv, "sum") == 0.0


def test_empty_dict_returns_zero():
    assert aggregate({}, "weighted_mean") == 0.0


def test_unknown_rule_raises():
    bv = {"US": 1, "EU": 2, "CN": 3, "RoW": 4}
    with pytest.raises(ValueError, match="unknown aggregation rule"):
        aggregate(bv, "average")


def test_valid_rules_set():
    assert VALID_RULES == {"leader", "weighted_mean", "max", "sum"}
