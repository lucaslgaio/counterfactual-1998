"""Null-treatment configuration and runner.

The null treatment runs the engine in a counterfactual where the AI big-bang
does NOT happen: ``ai_capability.frontier_capability`` is held at a low value
(~15) for every block at every turn. Other dynamics evolve normally — this
gives us a baseline trajectory we can compare to historical reality (where
the big-bang also didn't happen, so the null world is *our* world).

Calibration's job: find alphas that make the null-treatment trajectory match
historical data. Once calibrated, switching to big-bang mode reveals what
the AI shock would have done.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from src.engine.simulation import Simulation, SimulationConfig
from src.engine.state import BLOCKS, WorldState
from src.engine.turn_runner import TurnResult


# Frontier capability value held constant in null mode. Roughly the
# pre-1998 baseline: ML existed but wasn't generative-scale.
NULL_FRONTIER_VALUE = 15.0


@dataclass
class NullTreatmentConfig:
    """Knobs for the null-treatment run."""

    seed: int = 42
    null_frontier_value: float = NULL_FRONTIER_VALUE
    shock_overall_probability: float = 0.5  # half the default shock rate
    n_runs: int = 3  # average across runs to reduce stochastic variance


def make_null_treatment_config(seed: int = 42, n_runs: int = 3) -> NullTreatmentConfig:
    return NullTreatmentConfig(seed=seed, n_runs=n_runs)


def _pin_frontier_capability(state: WorldState, value: float) -> WorldState:
    """Return a new WorldState with frontier_capability fixed at ``value`` for all blocks."""
    new_block = {k: dict(v) for k, v in state.block_metrics.items()}
    if "ai_capability.frontier_capability" in new_block:
        new_block["ai_capability.frontier_capability"] = {b: float(value) for b in BLOCKS}
    return WorldState(
        turn_index=state.turn_index,
        turn_label=state.turn_label,
        global_metrics=dict(state.global_metrics),
        block_metrics=new_block,
        matrix_metrics={k: dict(v) for k, v in state.matrix_metrics.items()},
        metadata=dict(state.metadata),
    )


def run_null_treatment_once(
    sim_config: SimulationConfig,
    null_config: NullTreatmentConfig,
    n_turns: int = 57,
) -> List[TurnResult]:
    """Run a single null-treatment trajectory.

    Frontier capability is pinned to ``null_frontier_value`` BEFORE every
    turn (overriding whatever the previous turn's deltas would have produced).
    This is implemented by wrapping the simulation: we re-set the state at
    every iteration. It costs nothing extra in compute and matches the user's
    "interceptar antes de cada turno" requirement.
    """
    sim = Simulation(config=sim_config)
    # Pin initial frontier
    sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
    results: List[TurnResult] = []
    for _ in range(n_turns):
        # Pin before turn
        sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
        result = sim.run_turn()
        # Pin after turn (so state_after also reflects null)
        sim.state = _pin_frontier_capability(sim.state, null_config.null_frontier_value)
        # Also overwrite the captured state_after on the TurnResult so callers
        # who inspect the trajectory see the pinned value (not the post-edge
        # value that the engine produced).
        result.state_after = _pin_frontier_capability(
            result.state_after, null_config.null_frontier_value
        )
        results.append(result)
    return results


def run_null_treatment(
    null_config: NullTreatmentConfig,
    seed_offset: int = 0,
    n_turns: int = 57,
) -> List[List[TurnResult]]:
    """Run ``null_config.n_runs`` independent trajectories with seeds derived
    from the base seed.
    """
    runs: List[List[TurnResult]] = []
    for i in range(null_config.n_runs):
        cfg = SimulationConfig(
            seed=null_config.seed + seed_offset * 7919 + i * 1009,
            shock_overall_probability=null_config.shock_overall_probability,
        )
        runs.append(run_null_treatment_once(cfg, null_config, n_turns=n_turns))
    return runs


# ---------------------------------------------------------------------------- extraction


def extract_metric_trajectory(
    runs: List[List[TurnResult]],
    metric_key: str,
    block: Optional[str] = None,
) -> np.ndarray:
    """Return the mean trajectory across runs for one metric.

    Output shape: (n_turns + 1,) where the +1 is the initial state.

    For block-specific extraction: pass ``block`` (e.g. ``"US"``).
    For globals: leave block=None.
    """
    if not runs:
        return np.array([])
    n_turns = len(runs[0])
    n_points = n_turns + 1  # initial state + after each turn
    matrix = np.zeros((len(runs), n_points), dtype=float)
    for r_idx, run in enumerate(runs):
        # initial state
        s0 = run[0].state_before
        matrix[r_idx, 0] = _read_metric(s0, metric_key, block)
        for t_idx, r in enumerate(run):
            matrix[r_idx, t_idx + 1] = _read_metric(r.state_after, metric_key, block)
    return matrix.mean(axis=0)


def _read_metric(state: WorldState, metric_key: str, block: Optional[str]) -> float:
    if metric_key in state.global_metrics:
        return float(state.global_metrics[metric_key])
    if metric_key in state.block_metrics:
        if block:
            return float(state.block_metrics[metric_key].get(block, np.nan))
        # No block specified — return weighted mean
        from src.engine.aggregation import aggregate
        return float(aggregate(state.block_metrics[metric_key], "weighted_mean"))
    if metric_key in state.matrix_metrics:
        return float(state.matrix_metrics[metric_key].get("total", np.nan))
    return float("nan")
