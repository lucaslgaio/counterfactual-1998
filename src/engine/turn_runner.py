"""Orchestrate one full turn: sample → compute deltas → apply → clamp.

Pure functional core; all randomness comes from the supplied numpy.random.Generator.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from src.engine.clamp import MetricRanges, clamp_state
from src.engine.delta_computer import DeltaPackage, SpecBundle, compute_turn_deltas
from src.engine.event_sampler import SampledEvent, sample_event
from src.engine.shock_sampler import (
    DEFAULT_SHOCK_CATALOG,
    ExogenousShock,
    SampledShock,
    sample_shock,
)
from src.engine.state import BLOCKS, TURN_LABELS, WorldState


@dataclass
class SimulationConfig:
    """Top-level knobs for a run."""

    seed: int = 42
    shock_overall_probability: float = 1.0
    shock_catalog: Optional[List[ExogenousShock]] = None  # default if None
    diffusion_alpha: float = 0.05  # for spillover (kept here for visibility)


@dataclass
class TurnResult:
    """Everything that happened during one turn — what frontend Lovable consumes."""

    turn_index: int
    turn_label: str
    state_before: WorldState
    state_after: WorldState
    delta_package: DeltaPackage
    sampled_event: Optional[SampledEvent]
    sampled_shock: Optional[SampledShock]
    user_input_deltas: Dict[str, float] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "turn_index": self.turn_index,
            "turn_label": self.turn_label,
            "state_before": self.state_before.to_json(),
            "state_after": self.state_after.to_json(),
            "delta_package": self.delta_package.to_json(),
            "sampled_event": self.sampled_event.to_json() if self.sampled_event else None,
            "sampled_shock": self.sampled_shock.to_json() if self.sampled_shock else None,
            "user_input_deltas": dict(self.user_input_deltas),
        }


# Per-turn growth cap (positive direction only). Acts as a safety net before
# calibration (Etapa 5). With this cap, no metric can grow more than this
# fraction of its current value (or absolute floor) per turn. Negative deltas
# are NOT capped — decay flows freely.
# Per-turn growth cap on edge-derived deltas. With 1.5%/turn, 58-turn
# cumulative growth from edge dynamics alone is ~2.4x, which keeps metrics
# bounded enough to leave headroom for exogenous events/shocks to be
# visible. Tightening further muffles edge dynamics; loosening lets edges
# saturate and crowd out variance. Pre-calibration safety net only.
MAX_POSITIVE_GROWTH_RATIO = 0.015
MAX_NEGATIVE_GROWTH_RATIO = 0.015  # symmetric — prevents decay-to-zero
MIN_ABSOLUTE_GROWTH = 0.3  # absolute floor so tiny metrics can move at all


def _cap_edge_delta(current: float, delta: float) -> float:
    """Cap an edge-derived delta symmetrically. Positive deltas can't exceed
    ``max(MIN_ABSOLUTE_GROWTH, MAX_POSITIVE_GROWTH_RATIO*|current|)``; negative
    deltas can't be more negative than the equivalent floor.

    This is a safety net before Etapa 5 calibration — it prevents both
    saturation-explosion and decay-to-zero from edge dynamics dominating
    the simulation.
    """
    if delta == 0:
        return 0.0
    if delta > 0:
        cap = max(MIN_ABSOLUTE_GROWTH, MAX_POSITIVE_GROWTH_RATIO * abs(current))
        return min(delta, cap)
    cap = -max(MIN_ABSOLUTE_GROWTH, MAX_NEGATIVE_GROWTH_RATIO * abs(current))
    return max(delta, cap)


# Backwards-compatible alias used elsewhere in the file
_cap_positive_growth = _cap_edge_delta


def _apply_deltas_to_state(
    state: WorldState, pkg: DeltaPackage, ranges: MetricRanges
) -> WorldState:
    """Apply deltas, then clamp. Both produce new state objects (immutability).

    Edge-derived positive deltas are capped by ``MAX_POSITIVE_GROWTH_RATIO``
    (safety net pre-calibration). Exogenous deltas (events, shocks, user
    input) bypass the cap — they're discrete, intentional, spec-authored.
    """
    new_global = dict(state.global_metrics)
    for key in set(pkg.edge_global_deltas) | set(pkg.exogenous_global_deltas):
        current = new_global.get(key, 0.0)
        edge_d = _cap_positive_growth(current, pkg.edge_global_deltas.get(key, 0.0))
        exo_d = pkg.exogenous_global_deltas.get(key, 0.0)
        new_global[key] = current + edge_d + exo_d

    new_block: Dict[str, Dict[str, float]] = {
        k: dict(v) for k, v in state.block_metrics.items()
    }
    metrics_block = set(pkg.edge_block_deltas) | set(pkg.exogenous_block_deltas)
    for metric_key in metrics_block:
        new_block.setdefault(metric_key, {})
        edge_subdict = pkg.edge_block_deltas.get(metric_key, {})
        exo_subdict = pkg.exogenous_block_deltas.get(metric_key, {})
        for block in set(edge_subdict) | set(exo_subdict):
            current = new_block[metric_key].get(block, 0.0)
            edge_d = _cap_positive_growth(current, edge_subdict.get(block, 0.0))
            exo_d = exo_subdict.get(block, 0.0)
            new_block[metric_key][block] = current + edge_d + exo_d

    new_matrix: Dict[str, Dict[str, float]] = {
        k: dict(v) for k, v in state.matrix_metrics.items()
    }
    metrics_matrix = set(pkg.edge_matrix_deltas) | set(pkg.exogenous_matrix_deltas)
    for metric_key in metrics_matrix:
        new_matrix.setdefault(metric_key, {})
        edge_subdict = pkg.edge_matrix_deltas.get(metric_key, {})
        exo_subdict = pkg.exogenous_matrix_deltas.get(metric_key, {})
        for pair in set(edge_subdict) | set(exo_subdict):
            current = new_matrix[metric_key].get(pair, 0.0)
            edge_d = _cap_positive_growth(current, edge_subdict.get(pair, 0.0))
            exo_d = exo_subdict.get(pair, 0.0)
            new_matrix[metric_key][pair] = current + edge_d + exo_d

    next_idx = state.turn_index + 1
    if next_idx >= len(TURN_LABELS):
        next_idx = state.turn_index
    raw = WorldState(
        turn_index=next_idx,
        turn_label=TURN_LABELS[next_idx],
        global_metrics=new_global,
        block_metrics=new_block,
        matrix_metrics=new_matrix,
        metadata=copy.deepcopy(state.metadata),
    )
    return clamp_state(raw, ranges)


def run_turn(
    state: WorldState,
    config: SimulationConfig,
    spec: SpecBundle,
    ranges: MetricRanges,
    rng: np.random.Generator,
    user_input_deltas: Optional[Dict[str, float]] = None,
) -> TurnResult:
    """Execute one full turn and return the result.

    The state passed in is the state AT the start of the turn (i.e., before
    the turn's deltas are applied). The returned TurnResult.state_after is
    the state at the end of the turn (with new turn_index/turn_label).
    """
    # 1. Sample event for this turn
    event = sample_event(state.turn_label, state, rng, spec.events_spec)
    # 2. Sample shock
    shock = sample_shock(
        rng,
        catalog=config.shock_catalog or DEFAULT_SHOCK_CATALOG,
        overall_probability=config.shock_overall_probability,
    )
    # 3. Compute deltas
    pkg = compute_turn_deltas(state, event, shock, user_input_deltas, spec)
    # 4. Apply deltas with clamping
    new_state = _apply_deltas_to_state(state, pkg, ranges)

    # Annotate metadata on the new state for traceability
    new_state = new_state.with_metadata(
        previous_turn_label=state.turn_label,
        sampled_event_id=event.event_id if event else None,
        sampled_event_variant=event.variant_id if event else None,
        sampled_shock_id=shock.shock_id if shock else None,
    )

    return TurnResult(
        turn_index=state.turn_index,
        turn_label=state.turn_label,
        state_before=state,
        state_after=new_state,
        delta_package=pkg,
        sampled_event=event,
        sampled_shock=shock,
        user_input_deltas=dict(user_input_deltas or {}),
    )
