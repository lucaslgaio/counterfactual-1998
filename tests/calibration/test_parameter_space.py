"""Tests for src/calibration/parameter_space.py."""
from __future__ import annotations

import numpy as np

from src.calibration.parameter_space import (
    CalibratableParameter,
    apply_parameters_to_spec,
    build_parameter_space,
)
from src.engine.simulation import build_spec_bundle


def test_build_parameter_space_real_spec():
    spec = build_spec_bundle()
    ps = build_parameter_space(spec)
    # Expect 30-80 parameters depending on filtering
    assert 20 <= len(ps) <= 120, f"got {len(ps)} parameters"
    # Each parameter must have a valid range
    for p in ps:
        assert p.range_min < p.range_max
        assert p.range_min <= p.initial_value <= p.range_max


def test_high_confidence_range_is_narrower():
    spec = build_spec_bundle()
    ps = build_parameter_space(spec)
    high_widths = []
    medium_widths = []
    for p in ps:
        width_pct = (
            (p.range_max - p.range_min) / max(abs(p.initial_value), 1e-6)
            if p.initial_value != 0
            else 0
        )
        if p.confidence == "high":
            high_widths.append(width_pct)
        elif p.confidence == "medium":
            medium_widths.append(width_pct)
    if high_widths and medium_widths:
        assert np.mean(high_widths) < np.mean(medium_widths) + 1e-6


def test_target_metrics_filter_reduces_count():
    spec = build_spec_bundle()
    full = build_parameter_space(spec)
    # Restrict to a single target metric
    targets = {"energy_climate.co2_gt_year"}
    filtered = build_parameter_space(spec, target_metrics_with_data=targets)
    assert len(filtered) <= len(full)


def test_apply_parameters_returns_new_spec():
    spec = build_spec_bundle()
    ps = build_parameter_space(spec)[:5]
    alpha_vector = np.array([p.initial_value * 0.5 for p in ps])
    new_spec = apply_parameters_to_spec(spec, ps, alpha_vector)
    # The new spec must have updated values for those params
    for p, v in zip(ps, alpha_vector):
        assert new_spec.functions[p.edge_id].parameters[p.parameter_name] == v
    # The original spec must be untouched
    for p in ps:
        assert spec.functions[p.edge_id].parameters.get(p.parameter_name) != alpha_vector[
            ps.index(p)
        ] or spec.functions[p.edge_id].parameters[p.parameter_name] == p.initial_value
