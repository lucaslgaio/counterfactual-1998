"""Tests for src/calibration/sensitivity.py."""
from __future__ import annotations

import numpy as np

from src.calibration.historical_loader import load_all_series
from src.calibration.null_treatment import make_null_treatment_config
from src.calibration.parameter_space import build_parameter_space
from src.calibration.sensitivity import _classify, sensitivity_analysis
from src.engine.simulation import build_spec_bundle


def test_classify_thresholds():
    assert _classify(2.0) == "critical"
    assert _classify(0.5) == "important"
    assert _classify(0.1) == "robust"
    assert _classify(-2.0) == "critical"  # absolute value


def test_sensitivity_runs_and_classifies():
    spec = build_spec_bundle()
    historical = load_all_series()
    ps = build_parameter_space(
        spec, target_metrics_with_data={s.metric_key for s in historical.values()}
    )[:3]
    if not ps:
        return
    cfg = make_null_treatment_config(seed=42, n_runs=1)
    x = np.array([p.initial_value for p in ps])
    report = sensitivity_analysis(
        x, ps, spec, historical, cfg, perturbation=0.20
    )
    assert len(report.parameters) == len(ps)
    for p in report.parameters:
        assert p.classification in {"critical", "important", "robust"}


def test_sensitivity_summary_counts_match():
    spec = build_spec_bundle()
    historical = load_all_series()
    ps = build_parameter_space(
        spec, target_metrics_with_data={s.metric_key for s in historical.values()}
    )[:3]
    if not ps:
        return
    cfg = make_null_treatment_config(seed=42, n_runs=1)
    x = np.array([p.initial_value for p in ps])
    report = sensitivity_analysis(x, ps, spec, historical, cfg, perturbation=0.10)
    js = report.to_json()
    s = js["summary"]
    assert s["critical"] + s["important"] + s["robust"] == len(report.parameters)
