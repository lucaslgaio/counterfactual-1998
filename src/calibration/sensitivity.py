"""Sensitivity analysis: which calibrated alphas are critical, which robust.

Given calibrated alphas, perturb each one ±perturbation% one at a time and
measure how the objective changes. High dError/dAlpha → critical parameter
that needs literature backup; low → robust parameter we can trust without
fine-grained justification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from src.calibration.historical_loader import HistoricalSeries
from src.calibration.null_treatment import NullTreatmentConfig
from src.calibration.objective import objective_function
from src.calibration.parameter_space import CalibratableParameter
from src.engine.delta_computer import SpecBundle


@dataclass
class ParameterSensitivity:
    edge_id: str
    parameter_name: str
    calibrated_value: float
    elasticity: float  # |dObj/dAlpha| × |alpha/Obj|, average across +/- perturbation
    classification: str  # "critical", "important", "robust"
    obj_at_minus: float
    obj_at_plus: float

    def to_json(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "parameter_name": self.parameter_name,
            "calibrated_value": float(self.calibrated_value),
            "elasticity": float(self.elasticity),
            "classification": self.classification,
            "obj_at_minus": float(self.obj_at_minus),
            "obj_at_plus": float(self.obj_at_plus),
        }


@dataclass
class SensitivityReport:
    baseline_objective: float
    perturbation: float
    parameters: List[ParameterSensitivity] = field(default_factory=list)

    @property
    def critical(self) -> List[ParameterSensitivity]:
        return [p for p in self.parameters if p.classification == "critical"]

    @property
    def important(self) -> List[ParameterSensitivity]:
        return [p for p in self.parameters if p.classification == "important"]

    @property
    def robust(self) -> List[ParameterSensitivity]:
        return [p for p in self.parameters if p.classification == "robust"]

    def to_json(self) -> dict:
        return {
            "baseline_objective": self.baseline_objective,
            "perturbation": self.perturbation,
            "parameters": [p.to_json() for p in self.parameters],
            "summary": {
                "critical": len(self.critical),
                "important": len(self.important),
                "robust": len(self.robust),
            },
        }


def _classify(elasticity: float) -> str:
    a = abs(elasticity)
    if a > 1.0:
        return "critical"
    if a > 0.3:
        return "important"
    return "robust"


def sensitivity_analysis(
    calibrated_alphas: np.ndarray,
    parameter_space: List[CalibratableParameter],
    spec: SpecBundle,
    historical: Dict[str, HistoricalSeries],
    null_config: NullTreatmentConfig,
    weights: Optional[Dict[str, float]] = None,
    perturbation: float = 0.20,
) -> SensitivityReport:
    """One-at-a-time perturbation of each parameter; return classification.

    Elasticity is computed as
        ((|f(α + dα) − f(α)| + |f(α − dα) − f(α)|) / 2) × (|α| / |f(α)|) / |dα|
    which approximates |∂f/∂α × α / f| at the calibrated point.
    """

    def obj(x: np.ndarray) -> float:
        return objective_function(
            x,
            parameter_space,
            spec,
            historical,
            null_config,
            weights,
            regularization_lambda=0.0,  # exclude regularization for pure fit signal
        )

    baseline = obj(calibrated_alphas)
    report = SensitivityReport(baseline_objective=baseline, perturbation=perturbation)

    for i, p in enumerate(parameter_space):
        x_minus = calibrated_alphas.copy()
        x_plus = calibrated_alphas.copy()
        delta = abs(calibrated_alphas[i]) * perturbation
        if delta < 1e-9:  # parameter is essentially zero — fall back to absolute
            delta = perturbation
        x_minus[i] = max(p.range_min, calibrated_alphas[i] - delta)
        x_plus[i] = min(p.range_max, calibrated_alphas[i] + delta)
        f_minus = obj(x_minus)
        f_plus = obj(x_plus)
        # Elasticity (dimensionless)
        if baseline > 0 and abs(calibrated_alphas[i]) > 0:
            avg_diff = 0.5 * (abs(f_plus - baseline) + abs(f_minus - baseline))
            elasticity = (avg_diff / baseline) * abs(calibrated_alphas[i] / delta)
        else:
            elasticity = 0.0
        report.parameters.append(
            ParameterSensitivity(
                edge_id=p.edge_id,
                parameter_name=p.parameter_name,
                calibrated_value=float(calibrated_alphas[i]),
                elasticity=float(elasticity),
                classification=_classify(elasticity),
                obj_at_minus=float(f_minus),
                obj_at_plus=float(f_plus),
            )
        )
    return report
