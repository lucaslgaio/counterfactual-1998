"""Tests for src/calibration/error_metrics.py."""
from __future__ import annotations

import numpy as np

from src.calibration.error_metrics import (
    mae,
    mae_normalized,
    rmse,
    rmse_normalized,
    weighted_error,
)


def test_mae_zero_when_predicted_equals_observed():
    a = np.array([1.0, 2.0, 3.0])
    assert mae(a, a) == 0.0


def test_mae_proportional_to_offset():
    obs = np.array([1.0, 2.0, 3.0])
    pred = obs + 5.0
    assert mae(pred, obs) == 5.0


def test_mae_ignores_nan_in_observed():
    obs = np.array([1.0, np.nan, 3.0])
    pred = np.array([2.0, 99.0, 3.0])  # 99 should be ignored
    # Only positions 0 and 2 count: errors 1 and 0 → mean 0.5
    assert mae(pred, obs) == 0.5


def test_mae_normalized_divides_by_range():
    obs = np.array([10.0])
    pred = np.array([15.0])
    # MAE=5, range=100 → 0.05
    assert abs(mae_normalized(pred, obs, 100.0) - 0.05) < 1e-9


def test_mae_normalized_with_zero_range_returns_nan():
    e = mae_normalized(np.array([1.0]), np.array([2.0]), 0.0)
    assert np.isnan(e)


def test_rmse_basic():
    obs = np.array([1.0, 2.0, 3.0])
    pred = np.array([2.0, 3.0, 4.0])  # error=1 each → RMSE=1
    assert abs(rmse(pred, obs) - 1.0) < 1e-9


def test_weighted_error_aggregate():
    pred = {"a": np.array([1.0]), "b": np.array([10.0])}
    obs = {"a": np.array([1.0]), "b": np.array([15.0])}
    ranges = {"a": 100, "b": 100}
    weights = {"a": 1.0, "b": 1.0}
    agg, breakdown = weighted_error(pred, obs, ranges, weights)
    # series a: MAE=0/100 = 0; series b: MAE=5/100 = 0.05
    # Equal weights → average = 0.025
    assert abs(agg - 0.025) < 1e-9
    assert breakdown["b"] == 0.05


def test_weighted_error_skips_missing_series():
    pred = {"a": np.array([1.0])}
    obs = {"b": np.array([1.0])}  # different series id
    agg, breakdown = weighted_error(pred, obs, {"a": 100, "b": 100})
    # No overlap → 0
    assert agg == 0.0


def test_weighted_error_higher_weight_dominates():
    pred = {"a": np.array([1.0]), "b": np.array([10.0])}
    obs = {"a": np.array([1.0]), "b": np.array([15.0])}
    ranges = {"a": 100, "b": 100}
    weights_a = {"a": 10.0, "b": 1.0}
    weights_b = {"a": 1.0, "b": 10.0}
    agg_a, _ = weighted_error(pred, obs, ranges, weights_a)
    agg_b, _ = weighted_error(pred, obs, ranges, weights_b)
    # b has the larger error; weighting b higher should yield larger aggregate
    assert agg_b > agg_a
