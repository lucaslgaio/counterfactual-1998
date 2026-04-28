"""End-to-end calibration orchestrator.

Loads spec + historical data, builds parameter space, runs L-BFGS (and DE
if requested), runs sensitivity analysis, validates confidence constraints,
and persists all artifacts to ``runs/calibration/``.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.calibration.confidence_constraints import (
    at_boundary_count,
    validate_calibration_respects_confidence,
)
from src.calibration.error_metrics import weighted_error
from src.calibration.historical_loader import (
    HistoricalSeries,
    coverage_report,
    load_all_series,
)
from src.calibration.null_treatment import (
    NullTreatmentConfig,
    extract_metric_trajectory,
    make_null_treatment_config,
    run_null_treatment,
)
from src.calibration.objective import objective_function, _series_id, _range_lookup
from src.calibration.optimizer import CalibrationResult, calibrate
from src.calibration.parameter_space import (
    CalibratableParameter,
    apply_parameters_to_spec,
    build_parameter_space,
)
from src.calibration.sensitivity import sensitivity_analysis
from src.engine.simulation import build_spec_bundle

logger = logging.getLogger(__name__)


@dataclass
class CalibrationConfig:
    seed: int = 42
    n_runs_per_eval: int = 3
    max_lbfgs_iterations: int = 60
    max_de_iterations: int = 20
    use_de: bool = True
    regularization_lambda: float = 0.01
    sensitivity_perturbation: float = 0.20
    n_turns: int = 57


def _weights_from_confidence(historical: Dict[str, HistoricalSeries]) -> Dict[str, float]:
    """High-confidence series weigh more in the objective."""
    return {sid: float(s.confidence) for sid, s in historical.items()}


def _target_metrics_from_historical(historical: Dict[str, HistoricalSeries]) -> set:
    """Set of base metric_keys (no block suffix) we have data for."""
    return {s.metric_key for s in historical.values()}


def run_full_calibration(
    output_dir: Path,
    config: Optional[CalibrationConfig] = None,
    spec_dir: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> dict:
    """Run the full calibration pipeline and persist artifacts.

    Returns a summary dict (same data as the persisted ``calibration_summary.json``).
    """
    config = config or CalibrationConfig()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    spec = build_spec_bundle(spec_dir) if spec_dir else build_spec_bundle()
    if data_dir is None:
        from src.calibration.historical_loader import DEFAULT_DATA_DIR
        data_dir = DEFAULT_DATA_DIR
    historical = load_all_series(data_dir)
    if not historical:
        raise RuntimeError(f"no usable historical series found in {data_dir}")

    logger.info("loaded %d historical series", len(historical))
    coverage = coverage_report(historical)

    targets = _target_metrics_from_historical(historical)
    parameter_space = build_parameter_space(spec, target_metrics_with_data=targets)
    logger.info("parameter space: %d parameters", len(parameter_space))

    null_config = make_null_treatment_config(seed=config.seed, n_runs=config.n_runs_per_eval)
    weights = _weights_from_confidence(historical)

    chosen, alternate = calibrate(
        parameter_space=parameter_space,
        spec=spec,
        historical=historical,
        null_config=null_config,
        weights=weights,
        regularization_lambda=config.regularization_lambda,
        use_de=config.use_de,
        max_lbfgs=config.max_lbfgs_iterations,
        max_de=config.max_de_iterations,
    )
    logger.info(
        "calibration complete: method=%s, final_obj=%.4f, initial_obj=%.4f",
        chosen.method,
        chosen.final_objective,
        chosen.initial_objective,
    )

    # Sensitivity analysis on the chosen result.
    sensitivity = sensitivity_analysis(
        chosen.alpha_vector,
        parameter_space,
        spec,
        historical,
        null_config,
        weights=weights,
        perturbation=config.sensitivity_perturbation,
    )

    # Confidence constraints check.
    violations = validate_calibration_respects_confidence(chosen.alpha_vector, parameter_space)
    boundary_n = at_boundary_count(chosen.alpha_vector, parameter_space)

    # Compute per-series fit with calibrated alphas.
    new_spec = apply_parameters_to_spec(spec, parameter_space, chosen.alpha_vector)
    runs = _final_run(new_spec, null_config, n_turns=config.n_turns)
    predicted = {
        _series_id(s.metric_key, s.block): extract_metric_trajectory(runs, s.metric_key, s.block)[
            : len(s.values)
        ]
        for s in historical.values()
    }
    observed = {sid: s.values for sid, s in historical.items()}
    ranges = _range_lookup(historical, spec)
    final_fit, breakdown = weighted_error(predicted, observed, ranges, weights)

    # Build alphas dict (edge_id:parameter_name → calibrated_value).
    alphas_dict = {p.key: float(v) for p, v in zip(parameter_space, chosen.alpha_vector)}
    initial_dict = {p.key: float(p.initial_value) for p in parameter_space}

    # Persist artifacts.
    (output_dir / "alphas_calibrated.json").write_text(
        json.dumps(
            {
                "method": chosen.method,
                "final_objective": chosen.final_objective,
                "initial_objective": chosen.initial_objective,
                "alphas": alphas_dict,
                "initial_values": initial_dict,
            },
            indent=2,
        )
    )
    (output_dir / "fit_report.json").write_text(
        json.dumps(
            {
                "weighted_error": final_fit,
                "per_series_mae_normalized": breakdown,
                "coverage": coverage,
                "violations": [v.to_json() for v in violations],
                "at_boundary_count": boundary_n,
            },
            indent=2,
        )
    )
    (output_dir / "sensitivity_report.json").write_text(
        json.dumps(sensitivity.to_json(), indent=2)
    )
    if alternate:
        (output_dir / "alternate_method.json").write_text(json.dumps(alternate.to_json(), indent=2))

    # Save the null-treatment trajectory under calibrated alphas.
    null_trajectories = {
        sid: list(map(float, traj.tolist()))
        for sid, traj in predicted.items()
    }
    (output_dir / "null_treatment_run.json").write_text(
        json.dumps({"trajectories": null_trajectories}, indent=2)
    )

    summary = {
        "method": chosen.method,
        "n_parameters": len(parameter_space),
        "final_objective": chosen.final_objective,
        "initial_objective": chosen.initial_objective,
        "improvement_pct": (
            100.0 * (chosen.initial_objective - chosen.final_objective) / chosen.initial_objective
            if chosen.initial_objective > 0
            else 0.0
        ),
        "weighted_error": final_fit,
        "violations_total": len(violations),
        "at_boundary_count": boundary_n,
        "sensitivity_summary": sensitivity.to_json()["summary"],
        "n_series": len(historical),
        "seconds_elapsed": chosen.seconds_elapsed,
    }
    (output_dir / "calibration_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def _final_run(spec, null_config, n_turns: int = 57):
    """Internal helper — same loop the objective uses, but for the final run."""
    from src.calibration.null_treatment import _pin_frontier_capability
    from src.engine.simulation import Simulation
    from src.engine.turn_runner import SimulationConfig

    runs = []
    for run_idx in range(null_config.n_runs):
        cfg = SimulationConfig(
            seed=null_config.seed + run_idx * 1009,
            shock_overall_probability=null_config.shock_overall_probability,
        )
        sim = Simulation(config=cfg, spec=spec)
        sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
        results = []
        for _ in range(n_turns):
            sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
            r = sim.run_turn()
            sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
            r.state_after = _pin_frontier_capability(r.state_after, null_config.null_frontier_value)
            results.append(r)
        runs.append(results)
    return runs
