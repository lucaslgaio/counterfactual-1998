"""Objective function for the optimizer.

Given an alpha vector + parameter_space + spec + historical data + null
config, returns a scalar weighted error. Lower is better. Adds an L1
regularization term that penalizes drift away from the spec's initial
values, so the optimizer doesn't wander into territory unsupported by
literature.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np

from src.calibration.error_metrics import weighted_error
from src.calibration.historical_loader import HistoricalSeries
from src.calibration.null_treatment import (
    NullTreatmentConfig,
    extract_metric_trajectory,
    run_null_treatment,
)
from src.calibration.parameter_space import (
    CalibratableParameter,
    apply_parameters_to_spec,
)
from src.engine.delta_computer import SpecBundle


def _series_id(metric_key: str, block: Optional[str]) -> str:
    if block is None or block == "":
        return metric_key
    return f"{metric_key}.{block}"


def _build_predicted_trajectories(
    runs,
    historical: Dict[str, HistoricalSeries],
) -> Dict[str, np.ndarray]:
    """For each historical series, extract the matching trajectory from runs.

    The simulation produces 58 turns (initial + 57 transitions). historical
    series have 58 rows. We align them.
    """
    preds: Dict[str, np.ndarray] = {}
    for sid, series in historical.items():
        pred = extract_metric_trajectory(runs, series.metric_key, series.block)
        # Trim/pad to len(series.values) (=58)
        target_n = len(series.values)
        if len(pred) >= target_n:
            preds[sid] = pred[:target_n]
        else:
            padded = np.full(target_n, np.nan)
            padded[: len(pred)] = pred
            preds[sid] = padded
    return preds


def regularization_term(
    alpha_vector: np.ndarray,
    parameter_space: List[CalibratableParameter],
    lambda_reg: float,
) -> float:
    """L1 distance from each parameter's initial value, weighted by lambda."""
    if lambda_reg <= 0:
        return 0.0
    total = 0.0
    for v, p in zip(alpha_vector, parameter_space):
        scale = max(abs(p.initial_value), 1e-6)
        total += abs(v - p.initial_value) / scale
    return float(lambda_reg * total / max(1, len(parameter_space)))


def objective_function(
    alpha_vector: np.ndarray,
    parameter_space: List[CalibratableParameter],
    spec: SpecBundle,
    historical: Dict[str, HistoricalSeries],
    null_config: NullTreatmentConfig,
    weights: Optional[Dict[str, float]] = None,
    regularization_lambda: float = 0.01,
    n_turns: int = 57,
) -> float:
    """Scalar to minimize.

    1. Apply alpha_vector → produce a SpecBundle with updated functions.
    2. Run null treatment (n_runs trajectories, averaged).
    3. Extract predicted trajectories per historical series.
    4. Compute weighted MAE_normalized; add regularization.
    """
    new_spec = apply_parameters_to_spec(spec, parameter_space, alpha_vector)

    # Patch the simulation to use the new spec. Since Simulation doesn't
    # accept a spec at run time but uses SimulationConfig, we monkey-patch
    # via a thread-local or override. Simplest: override the build_spec_bundle
    # caching path. For MVP we re-use new_spec directly via Simulation
    # constructor with explicit spec=.
    from src.engine.simulation import Simulation
    from src.engine.turn_runner import SimulationConfig

    runs = []
    for run_idx in range(null_config.n_runs):
        cfg = SimulationConfig(
            seed=null_config.seed + run_idx * 1009,
            shock_overall_probability=null_config.shock_overall_probability,
        )
        sim = Simulation(config=cfg, spec=new_spec)
        # Pin frontier capability before each turn
        from src.calibration.null_treatment import _pin_frontier_capability

        sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
        results = []
        for _ in range(n_turns):
            sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
            r = sim.run_turn()
            sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
            r.state_after = _pin_frontier_capability(r.state_after, null_config.null_frontier_value)
            results.append(r)
        runs.append(results)

    predicted = _build_predicted_trajectories(runs, historical)
    observed = {sid: s.values for sid, s in historical.items()}
    ranges = _range_lookup(historical, spec)

    fit_error, _ = weighted_error(predicted, observed, ranges, weights)
    reg = regularization_term(alpha_vector, parameter_space, regularization_lambda)
    return float(fit_error + reg)


def _range_lookup(
    historical: Dict[str, HistoricalSeries], spec: SpecBundle
) -> Dict[str, float]:
    """Return ``{series_id: range_max}``, used to normalize MAE per metric."""
    out: Dict[str, float] = {}
    for sid, series in historical.items():
        rng = spec.metric_ranges.get(series.metric_key, (0.0, 1.0))
        out[sid] = float(rng[1] - rng[0])
    return out
