"""Tests for src/calibration/optimizer.py.

These run against the real spec but with very small parameter spaces and
short horizons so they finish in seconds, not minutes.
"""
from __future__ import annotations

import numpy as np

from src.calibration.historical_loader import load_all_series
from src.calibration.null_treatment import make_null_treatment_config
from src.calibration.optimizer import (
    CalibrationResult,
    calibrate_lbfgs,
)
from src.calibration.parameter_space import build_parameter_space
from src.engine.simulation import build_spec_bundle


def _small_parameter_space():
    spec = build_spec_bundle()
    historical = load_all_series()
    ps = build_parameter_space(
        spec, target_metrics_with_data={s.metric_key for s in historical.values()}
    )
    return spec, historical, ps[:3]


def test_lbfgs_returns_calibration_result():
    spec, historical, ps = _small_parameter_space()
    if not ps:
        return  # nothing to calibrate; skip
    cfg = make_null_treatment_config(seed=42, n_runs=1)
    result = calibrate_lbfgs(ps, spec, historical, cfg, max_iterations=3)
    assert isinstance(result, CalibrationResult)
    assert result.method == "L-BFGS-B"
    assert np.isfinite(result.final_objective)
    # Final objective should be ≤ initial (or essentially equal — depends on starting point)
    assert result.final_objective <= result.initial_objective + 1e-6


def test_lbfgs_alpha_vector_within_bounds():
    spec, historical, ps = _small_parameter_space()
    if not ps:
        return
    cfg = make_null_treatment_config(seed=42, n_runs=1)
    result = calibrate_lbfgs(ps, spec, historical, cfg, max_iterations=3)
    for v, p in zip(result.alpha_vector, ps):
        assert p.range_min - 1e-6 <= v <= p.range_max + 1e-6
