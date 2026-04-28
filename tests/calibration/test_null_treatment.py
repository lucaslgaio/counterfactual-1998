"""Tests for src/calibration/null_treatment.py."""
from __future__ import annotations

import numpy as np

from src.calibration.null_treatment import (
    NullTreatmentConfig,
    extract_metric_trajectory,
    make_null_treatment_config,
    run_null_treatment,
    run_null_treatment_once,
)
from src.engine.turn_runner import SimulationConfig


def test_make_null_treatment_config_defaults():
    cfg = make_null_treatment_config(seed=42, n_runs=2)
    assert cfg.seed == 42
    assert cfg.n_runs == 2
    assert cfg.null_frontier_value > 0


def test_run_null_treatment_pins_frontier():
    """Across the entire null run, frontier_capability stays at the pinned
    value for every block at every turn."""
    null_cfg = NullTreatmentConfig(seed=42, null_frontier_value=15.0, n_runs=1)
    sim_cfg = SimulationConfig(seed=42)
    results = run_null_treatment_once(sim_cfg, null_cfg, n_turns=10)
    for r in results:
        for block, val in r.state_after.block_metrics["ai_capability.frontier_capability"].items():
            assert abs(val - 15.0) < 1e-9, f"frontier {block}={val} not pinned"


def test_run_null_treatment_returns_n_runs():
    cfg = make_null_treatment_config(seed=42, n_runs=3)
    runs = run_null_treatment(cfg, n_turns=5)
    assert len(runs) == 3
    for run in runs:
        assert len(run) == 5


def test_extract_metric_trajectory_global():
    cfg = make_null_treatment_config(seed=42, n_runs=2)
    runs = run_null_treatment(cfg, n_turns=10)
    traj = extract_metric_trajectory(runs, "energy_climate.co2_gt_year")
    # Should have n_turns+1 points (initial + after each turn)
    assert len(traj) == 11
    assert not np.any(np.isnan(traj))


def test_extract_metric_trajectory_block_specific():
    cfg = make_null_treatment_config(seed=42, n_runs=2)
    runs = run_null_treatment(cfg, n_turns=5)
    traj = extract_metric_trajectory(
        runs, "ai_capability.frontier_capability", block="US"
    )
    # All values should equal the pinned value
    assert np.all(np.abs(traj - 15.0) < 1e-9)


def test_run_null_treatment_deterministic_with_same_seed():
    cfg = make_null_treatment_config(seed=42, n_runs=1)
    runs_a = run_null_treatment(cfg, n_turns=5)
    runs_b = run_null_treatment(cfg, n_turns=5)
    # Same seed → same trajectory for at least one metric
    traj_a = extract_metric_trajectory(runs_a, "financial_markets.global_index")
    traj_b = extract_metric_trajectory(runs_b, "financial_markets.global_index")
    assert np.allclose(traj_a, traj_b)
