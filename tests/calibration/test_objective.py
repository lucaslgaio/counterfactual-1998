"""Tests for src/calibration/objective.py."""
from __future__ import annotations

import numpy as np

from src.calibration.historical_loader import load_all_series
from src.calibration.null_treatment import make_null_treatment_config
from src.calibration.objective import objective_function, regularization_term
from src.calibration.parameter_space import build_parameter_space
from src.engine.simulation import build_spec_bundle


def test_regularization_term_zero_when_at_initial():
    spec = build_spec_bundle()
    ps = build_parameter_space(spec)[:5]
    initial = np.array([p.initial_value for p in ps])
    r = regularization_term(initial, ps, lambda_reg=0.1)
    assert r == 0.0


def test_regularization_term_grows_with_distance():
    spec = build_spec_bundle()
    ps = build_parameter_space(spec)[:5]
    initial = np.array([p.initial_value for p in ps])
    perturbed = initial + np.array([abs(p.initial_value) * 0.5 for p in ps])
    r0 = regularization_term(initial, ps, lambda_reg=0.1)
    r1 = regularization_term(perturbed, ps, lambda_reg=0.1)
    assert r1 > r0


def test_objective_returns_finite_scalar():
    spec = build_spec_bundle()
    historical = load_all_series()
    ps = build_parameter_space(spec, target_metrics_with_data={s.metric_key for s in historical.values()})[:10]
    if not ps:
        return  # nothing to calibrate; skip
    cfg = make_null_treatment_config(seed=42, n_runs=1)
    x = np.array([p.initial_value for p in ps])
    val = objective_function(x, ps, spec, historical, cfg, n_turns=5)
    assert np.isfinite(val)


def test_objective_is_deterministic_given_seed():
    """Same x → same output; cornerstone for any optimizer to converge."""
    spec = build_spec_bundle()
    historical = load_all_series()
    ps = build_parameter_space(spec, target_metrics_with_data={s.metric_key for s in historical.values()})[:5]
    if not ps:
        return
    cfg = make_null_treatment_config(seed=42, n_runs=1)
    x = np.array([p.initial_value for p in ps])
    a = objective_function(x, ps, spec, historical, cfg, n_turns=5)
    b = objective_function(x, ps, spec, historical, cfg, n_turns=5)
    assert abs(a - b) < 1e-9
