"""Validate that calibration results respect the confidence-based ranges
declared in the parameter_space. This is the bridge between Etapa 2's
methodological review (which assigned high/medium/low confidence to edges)
and Etapa 5's optimization (which must not push high-confidence edges far
from their literature-anchored defaults).

If the optimizer pushes a high-confidence parameter outside its range, that's
a warning sign: either the literature is wrong, or our data is wrong, or the
model structure is wrong. The user should investigate before trusting the
calibration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import numpy as np

from src.calibration.parameter_space import CalibratableParameter


@dataclass
class Violation:
    edge_id: str
    parameter_name: str
    confidence: str
    calibrated_value: float
    range_min: float
    range_max: float
    severity: str  # "minor" / "major"

    def to_json(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "parameter_name": self.parameter_name,
            "confidence": self.confidence or "unset",
            "calibrated_value": float(self.calibrated_value),
            "range_min": float(self.range_min),
            "range_max": float(self.range_max),
            "severity": self.severity,
        }


def _severity_for(p: CalibratableParameter) -> str:
    if p.is_high_confidence:
        return "major"
    if p.confidence == "medium":
        return "minor"
    return "minor"


def validate_calibration_respects_confidence(
    calibrated_alphas: np.ndarray,
    parameter_space: List[CalibratableParameter],
    tolerance: float = 1e-6,
) -> List[Violation]:
    """Return the list of parameters that landed outside their declared range.

    With L-BFGS-B + bounds, this should usually be empty (scipy enforces the
    bounds) but it can happen if the optimizer hit the boundary, or if the
    range was defined too tightly to admit any improvement. The function is
    a safety net.
    """
    out: List[Violation] = []
    for v, p in zip(calibrated_alphas, parameter_space):
        if v < p.range_min - tolerance or v > p.range_max + tolerance:
            out.append(
                Violation(
                    edge_id=p.edge_id,
                    parameter_name=p.parameter_name,
                    confidence=p.confidence or "unset",
                    calibrated_value=float(v),
                    range_min=p.range_min,
                    range_max=p.range_max,
                    severity=_severity_for(p),
                )
            )
    return out


def at_boundary_count(
    calibrated_alphas: np.ndarray,
    parameter_space: List[CalibratableParameter],
    boundary_fraction: float = 0.02,
) -> int:
    """Count parameters that landed within ``boundary_fraction`` of their
    range edge — a sign the optimizer wanted to go further but the bound
    blocked it. Heuristic for "calibration is constrained by literature".
    """
    n = 0
    for v, p in zip(calibrated_alphas, parameter_space):
        width = p.range_max - p.range_min
        if width <= 0:
            continue
        d_min = (v - p.range_min) / width
        d_max = (p.range_max - v) / width
        if d_min < boundary_fraction or d_max < boundary_fraction:
            n += 1
    return n
