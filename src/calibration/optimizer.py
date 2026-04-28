"""Optimizers for the calibration objective.

Strategy:
1. Run scipy's L-BFGS-B from the spec's initial alphas (fast, local).
2. Optionally run differential evolution from scratch (robust, global).
3. Return the better solution.

The objective function is expensive (n_runs simulations of 58 turns each),
so we keep iteration counts modest — 100 L-BFGS iters is typically enough
to converge to a local minimum.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import differential_evolution, minimize

from src.calibration.historical_loader import HistoricalSeries
from src.calibration.null_treatment import NullTreatmentConfig
from src.calibration.objective import objective_function
from src.calibration.parameter_space import CalibratableParameter
from src.engine.delta_computer import SpecBundle


@dataclass
class CalibrationResult:
    method: str  # "L-BFGS-B" or "differential_evolution"
    success: bool
    final_objective: float
    initial_objective: float
    alpha_vector: np.ndarray
    n_iterations: int
    seconds_elapsed: float
    message: str = ""

    def to_json(self) -> dict:
        return {
            "method": self.method,
            "success": self.success,
            "final_objective": self.final_objective,
            "initial_objective": self.initial_objective,
            "alpha_vector": [float(v) for v in self.alpha_vector],
            "n_iterations": self.n_iterations,
            "seconds_elapsed": self.seconds_elapsed,
            "message": self.message,
        }


def _make_obj(
    parameter_space: List[CalibratableParameter],
    spec: SpecBundle,
    historical: Dict[str, HistoricalSeries],
    null_config: NullTreatmentConfig,
    weights: Optional[Dict[str, float]],
    regularization_lambda: float,
):
    """Closure capturing all the static arguments so scipy sees fn(x)."""

    def fn(x: np.ndarray) -> float:
        return objective_function(
            x,
            parameter_space,
            spec,
            historical,
            null_config,
            weights,
            regularization_lambda,
        )

    return fn


def calibrate_lbfgs(
    parameter_space: List[CalibratableParameter],
    spec: SpecBundle,
    historical: Dict[str, HistoricalSeries],
    null_config: NullTreatmentConfig,
    weights: Optional[Dict[str, float]] = None,
    regularization_lambda: float = 0.01,
    max_iterations: int = 100,
) -> CalibrationResult:
    """Local optimization with L-BFGS-B, starting from spec's initial values."""
    bounds = [(p.range_min, p.range_max) for p in parameter_space]
    x0 = np.array([p.initial_value for p in parameter_space], dtype=float)
    fn = _make_obj(
        parameter_space, spec, historical, null_config, weights, regularization_lambda
    )
    initial_obj = fn(x0)
    t0 = time.time()
    result = minimize(
        fn,
        x0,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": max_iterations, "disp": False},
    )
    elapsed = time.time() - t0
    return CalibrationResult(
        method="L-BFGS-B",
        success=bool(result.success),
        final_objective=float(result.fun),
        initial_objective=float(initial_obj),
        alpha_vector=np.array(result.x, dtype=float),
        n_iterations=int(result.nit if hasattr(result, "nit") else 0),
        seconds_elapsed=elapsed,
        message=str(result.message),
    )


def calibrate_differential_evolution(
    parameter_space: List[CalibratableParameter],
    spec: SpecBundle,
    historical: Dict[str, HistoricalSeries],
    null_config: NullTreatmentConfig,
    weights: Optional[Dict[str, float]] = None,
    regularization_lambda: float = 0.01,
    max_iterations: int = 50,
    popsize: int = 8,
) -> CalibrationResult:
    """Global optimization with differential evolution. Slower but doesn't
    rely on the gradient — useful as a sanity check on L-BFGS results.
    """
    bounds = [(p.range_min, p.range_max) for p in parameter_space]
    x0 = np.array([p.initial_value for p in parameter_space], dtype=float)
    fn = _make_obj(
        parameter_space, spec, historical, null_config, weights, regularization_lambda
    )
    initial_obj = fn(x0)
    t0 = time.time()
    result = differential_evolution(
        fn,
        bounds,
        maxiter=max_iterations,
        popsize=popsize,
        seed=null_config.seed,
        tol=0.01,
        polish=False,  # save time; L-BFGS already polished
    )
    elapsed = time.time() - t0
    return CalibrationResult(
        method="differential_evolution",
        success=bool(result.success),
        final_objective=float(result.fun),
        initial_objective=float(initial_obj),
        alpha_vector=np.array(result.x, dtype=float),
        n_iterations=int(result.nit if hasattr(result, "nit") else 0),
        seconds_elapsed=elapsed,
        message=str(result.message),
    )


def calibrate(
    parameter_space: List[CalibratableParameter],
    spec: SpecBundle,
    historical: Dict[str, HistoricalSeries],
    null_config: NullTreatmentConfig,
    weights: Optional[Dict[str, float]] = None,
    regularization_lambda: float = 0.01,
    use_de: bool = True,
    max_lbfgs: int = 100,
    max_de: int = 30,
) -> Tuple[CalibrationResult, Optional[CalibrationResult]]:
    """Recommended end-to-end calibration: L-BFGS first, optionally DE for sanity.

    Returns (chosen_result, alternate_result_or_None). The chosen result is
    whichever method achieved the lower objective.
    """
    lbfgs = calibrate_lbfgs(
        parameter_space,
        spec,
        historical,
        null_config,
        weights,
        regularization_lambda,
        max_iterations=max_lbfgs,
    )
    if not use_de:
        return lbfgs, None
    de = calibrate_differential_evolution(
        parameter_space,
        spec,
        historical,
        null_config,
        weights,
        regularization_lambda,
        max_iterations=max_de,
    )
    # Pick whichever is better
    if de.final_objective < lbfgs.final_objective * 0.95:
        return de, lbfgs
    return lbfgs, de
