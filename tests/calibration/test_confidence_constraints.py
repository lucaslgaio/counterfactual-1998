"""Tests for src/calibration/confidence_constraints.py."""
from __future__ import annotations

import numpy as np

from src.calibration.confidence_constraints import (
    at_boundary_count,
    validate_calibration_respects_confidence,
)
from src.calibration.parameter_space import CalibratableParameter


def _param(eid="e_x", name="alpha", initial=0.3, lo=0.2, hi=0.4, conf="high"):
    return CalibratableParameter(
        edge_id=eid,
        parameter_name=name,
        initial_value=initial,
        range_min=lo,
        range_max=hi,
        confidence=conf,
        is_high_confidence=(conf == "high"),
    )


def test_no_violations_when_in_range():
    ps = [_param()]
    out_of = validate_calibration_respects_confidence(np.array([0.3]), ps)
    assert out_of == []


def test_violation_when_above_range():
    ps = [_param(lo=0.2, hi=0.4, conf="high")]
    out_of = validate_calibration_respects_confidence(np.array([0.5]), ps)
    assert len(out_of) == 1
    assert out_of[0].severity == "major"


def test_violation_severity_minor_for_medium_conf():
    ps = [_param(conf="medium")]
    out_of = validate_calibration_respects_confidence(np.array([0.5]), ps)
    assert out_of[0].severity == "minor"


def test_at_boundary_count_zero_when_central():
    ps = [_param(lo=0.2, hi=0.4, initial=0.3)]
    n = at_boundary_count(np.array([0.3]), ps, boundary_fraction=0.05)
    assert n == 0


def test_at_boundary_count_detects_edge_hits():
    ps = [_param(lo=0.2, hi=0.4, initial=0.3)]
    # Within 1% of upper bound
    n = at_boundary_count(np.array([0.398]), ps, boundary_fraction=0.05)
    assert n == 1
