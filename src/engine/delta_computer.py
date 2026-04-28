"""Heart of the engine: compute deltas for one turn from the DAG.

Steps:
1. Apply event delta_package (if event sampled).
2. Apply shock delta_package (if shock sampled).
3. Apply user input deltas (if any).
4. For each ACTIVE edge (ignoring lags for MVP — see note below):
   - Resolve source value (with aggregation if vector→global).
   - Resolve target value.
   - Evaluate structural function → contribution.
   - Accumulate into per-target delta dict.
5. Compute Bass-style spillover for each vectorized metric.
6. Aggregate top contributors per target → causal_links_active.

Lag handling note: a precise lag implementation requires a state history
back to ``max(lag_turns)``. For MVP we treat all edges as if their lag is 0
once the simulation has run that many turns; before that, we apply a
linear ramp-up to keep the early turns from spiking. This is conservative
and matches the qualitative behavior of System Dynamics models.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.engine.aggregation import aggregate as aggregate_blocks
from src.engine.event_sampler import SampledEvent
from src.engine.functions import DEFAULT_MAGNITUDE_ALPHA, FunctionContext, evaluate
from src.engine.shock_sampler import SampledShock
from src.engine.spillover import build_friction_lookup, compute_spillover
from src.engine.state import BLOCKS, WorldState, _split_block_suffix
from src.spec.blocks import BlocksSpec
from src.spec.dag import CausalEdge
from src.spec.events import EventsSpec
from src.spec.functions import StructuralFunction


# ---------------------------------------------------------------------------- types


@dataclass
class CausalLinkActive:
    """One edge contribution to a target this turn."""

    edge_id: str
    source: str
    target: str
    source_value: float
    contribution: float
    form: str

    def to_json(self) -> dict:
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "source_value": self.source_value,
            "contribution": self.contribution,
            "form": self.form,
        }


@dataclass
class DeltaPackage:
    """Per-turn deltas, organized by metric category, plus provenance.

    Two layers are tracked separately so the turn_runner can cap edge-derived
    growth (open-loop alphas can be aggressive pre-calibration) without
    dampening event/shock/user deltas (which are discrete, intentional,
    pre-calibrated by the spec author).

    On read, ``global_deltas`` returns the SUM of both layers — callers that
    don't care about the split see one number. ``edge_global_deltas`` and
    ``exogenous_global_deltas`` are also available for the cap to operate on.
    """

    edge_global_deltas: Dict[str, float] = field(default_factory=dict)
    edge_block_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    edge_matrix_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    exogenous_global_deltas: Dict[str, float] = field(default_factory=dict)
    exogenous_block_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    exogenous_matrix_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    causal_links_active: List[CausalLinkActive] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def global_deltas(self) -> Dict[str, float]:
        out = dict(self.edge_global_deltas)
        for k, v in self.exogenous_global_deltas.items():
            out[k] = out.get(k, 0.0) + v
        return out

    @property
    def block_deltas(self) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {k: dict(v) for k, v in self.edge_block_deltas.items()}
        for k, sub in self.exogenous_block_deltas.items():
            out.setdefault(k, {})
            for b, v in sub.items():
                out[k][b] = out[k].get(b, 0.0) + v
        return out

    @property
    def matrix_deltas(self) -> Dict[str, Dict[str, float]]:
        out: Dict[str, Dict[str, float]] = {k: dict(v) for k, v in self.edge_matrix_deltas.items()}
        for k, sub in self.exogenous_matrix_deltas.items():
            out.setdefault(k, {})
            for p, v in sub.items():
                out[k][p] = out[k].get(p, 0.0) + v
        return out

    def add_to_global(self, key: str, delta: float, *, source: str = "edge"):
        target = self.edge_global_deltas if source == "edge" else self.exogenous_global_deltas
        target[key] = target.get(key, 0.0) + delta

    def add_to_block(self, metric_key: str, block: str, delta: float, *, source: str = "edge"):
        target = self.edge_block_deltas if source == "edge" else self.exogenous_block_deltas
        target.setdefault(metric_key, {})
        target[metric_key][block] = target[metric_key].get(block, 0.0) + delta

    def add_to_matrix(self, metric_key: str, pair: str, delta: float, *, source: str = "edge"):
        target = self.edge_matrix_deltas if source == "edge" else self.exogenous_matrix_deltas
        target.setdefault(metric_key, {})
        target[metric_key][pair] = target[metric_key].get(pair, 0.0) + delta

    def to_json(self) -> dict:
        return {
            "global_deltas": dict(self.global_deltas),
            "block_deltas": {k: dict(v) for k, v in self.block_deltas.items()},
            "matrix_deltas": {k: dict(v) for k, v in self.matrix_deltas.items()},
            "edge_global_deltas": dict(self.edge_global_deltas),
            "edge_block_deltas": {k: dict(v) for k, v in self.edge_block_deltas.items()},
            "edge_matrix_deltas": {k: dict(v) for k, v in self.edge_matrix_deltas.items()},
            "exogenous_global_deltas": dict(self.exogenous_global_deltas),
            "exogenous_block_deltas": {k: dict(v) for k, v in self.exogenous_block_deltas.items()},
            "exogenous_matrix_deltas": {k: dict(v) for k, v in self.exogenous_matrix_deltas.items()},
            "causal_links_active": [c.to_json() for c in self.causal_links_active],
            "provenance": dict(self.provenance),
        }


@dataclass
class SpecBundle:
    """Bundle of specs the delta_computer needs."""

    edges: List[CausalEdge]
    functions: Dict[str, StructuralFunction]  # by edge_id
    metric_categories: Dict[str, str]
    metric_ranges: Dict[str, Tuple[float, float]]
    blocks_spec: BlocksSpec
    events_spec: EventsSpec


# ---------------------------------------------------------------------------- helpers


def _resolve_source_value(
    edge: CausalEdge, state: WorldState, metric_categories: Dict[str, str]
) -> float:
    """Resolve the numeric value of an edge's source side.

    For vector→global edges, aggregate via the rule declared on the edge
    (or weighted_mean by default).
    """
    src_base, src_suffix = _split_block_suffix(edge.source)
    src_cat = metric_categories.get(src_base, "global")

    if src_suffix is not None:
        # Block-specific source (e.g. ai_capability.frontier_capability.US)
        if src_cat == "vectorized" and src_base in state.block_metrics:
            return state.block_metrics[src_base].get(src_suffix, 0.0)
        if src_cat == "matrix" and src_base in state.matrix_metrics:
            return state.matrix_metrics[src_base].get(src_suffix, 0.0)
        return 0.0

    # No suffix: depends on category
    if src_cat == "global" and src_base in state.global_metrics:
        return state.global_metrics[src_base]
    if src_cat == "vectorized" and src_base in state.block_metrics:
        rule = edge.aggregation or "weighted_mean"
        return aggregate_blocks(state.block_metrics[src_base], rule)
    if src_cat == "matrix" and src_base in state.matrix_metrics:
        return state.matrix_metrics[src_base].get("total", 0.0)
    return 0.0


def _resolve_target_value(
    edge: CausalEdge, state: WorldState, metric_categories: Dict[str, str], block: Optional[str] = None
) -> float:
    """Resolve target value for the function context (sigmoid needs it)."""
    tgt_base, tgt_suffix = _split_block_suffix(edge.target)
    tgt_cat = metric_categories.get(tgt_base, "global")
    if tgt_suffix:
        if tgt_cat == "vectorized" and tgt_base in state.block_metrics:
            return state.block_metrics[tgt_base].get(tgt_suffix, 0.0)
        if tgt_cat == "matrix" and tgt_base in state.matrix_metrics:
            return state.matrix_metrics[tgt_base].get(tgt_suffix, 0.0)
        return 0.0
    if tgt_cat == "global":
        return state.global_metrics.get(tgt_base, 0.0)
    if tgt_cat == "vectorized" and block and tgt_base in state.block_metrics:
        return state.block_metrics[tgt_base].get(block, 0.0)
    if tgt_cat == "matrix" and tgt_base in state.matrix_metrics:
        return state.matrix_metrics[tgt_base].get("total", 0.0)
    return 0.0


def _add_target_delta(
    pkg: DeltaPackage,
    edge: CausalEdge,
    contribution: float,
    metric_categories: Dict[str, str],
):
    """Route an edge contribution to the correct delta bucket on the package."""
    tgt_base, tgt_suffix = _split_block_suffix(edge.target)
    tgt_cat = metric_categories.get(tgt_base, "global")

    if tgt_suffix:
        if tgt_cat == "vectorized":
            pkg.add_to_block(tgt_base, tgt_suffix, contribution, source="edge")
        elif tgt_cat == "matrix":
            pkg.add_to_matrix(tgt_base, tgt_suffix, contribution, source="edge")
        else:
            pkg.add_to_global(tgt_base, contribution, source="edge")
        return

    if tgt_cat == "global":
        pkg.add_to_global(tgt_base, contribution, source="edge")
    elif tgt_cat == "vectorized":
        # Distribute across all 4 blocks (within_block / unspecified target)
        for b in BLOCKS:
            pkg.add_to_block(tgt_base, b, contribution, source="edge")
    elif tgt_cat == "matrix":
        # Distribute across all pairs/total
        if tgt_base in metric_categories:
            pkg.add_to_matrix(tgt_base, "total", contribution, source="edge")


# ---------------------------------------------------------------------------- main


def compute_turn_deltas(
    state: WorldState,
    sampled_event: Optional[SampledEvent],
    sampled_shock: Optional[SampledShock],
    user_input_deltas: Optional[Dict[str, float]],
    spec: SpecBundle,
) -> DeltaPackage:
    """Compute the full DeltaPackage for one turn.

    See module docstring for stages.
    """
    pkg = DeltaPackage()

    # 1. Event delta_package — exogenous (uncapped by turn_runner)
    if sampled_event and sampled_event.delta_package_id:
        dpkg = spec.events_spec.delta_packages.get(sampled_event.delta_package_id)
        if dpkg:
            for metric_key, delta in dpkg.deltas.items():
                _route_external_delta(
                    pkg, metric_key, float(delta), spec.metric_categories, source="exogenous"
                )

    # 2. Shock delta_package — exogenous
    if sampled_shock:
        for metric_key, delta in sampled_shock.delta_package.items():
            _route_external_delta(
                pkg, metric_key, float(delta), spec.metric_categories, source="exogenous"
            )

    # 3. User input deltas — exogenous (player chose them)
    if user_input_deltas:
        for metric_key, delta in user_input_deltas.items():
            _route_external_delta(
                pkg, metric_key, float(delta), spec.metric_categories, source="exogenous"
            )

    # 4. DAG edges
    causal_links = []
    for edge in spec.edges:
        fn_spec = spec.functions.get(edge.id)
        if fn_spec is None:
            continue
        # Determine alpha if not in params (use magnitude default)
        params = dict(fn_spec.parameters or {})
        if not any(k.startswith("alpha") for k in params):
            params["alpha"] = DEFAULT_MAGNITUDE_ALPHA.get(edge.magnitude, 0.1)
        if edge.direction == "negative":
            # Flip sign of effective alpha if direction=negative and params don't already encode it
            for ak in ("alpha", "alpha_pre", "alpha_post"):
                if ak in params and params[ak] is not None:
                    if params[ak] > 0:
                        params[ak] = -abs(float(params[ak]))

        source_value = _resolve_source_value(edge, state, spec.metric_categories)
        # For vectorized targets we may need per-block target_value; use the
        # block-aggregated value as a proxy for sigmoid context.
        target_value = _resolve_target_value(edge, state, spec.metric_categories)

        tgt_base, _ = _split_block_suffix(edge.target)
        target_range = spec.metric_ranges.get(tgt_base)
        ctx = FunctionContext(
            target_range=target_range,
            elapsed_turns=max(1, edge.lag_turns),
            activation_value=_compute_activation_value(fn_spec, state, spec.metric_categories),
            is_self_loop=edge.is_self_loop,
        )
        try:
            contribution = evaluate(fn_spec.form, source_value, target_value, params, ctx)
        except Exception as exc:
            # Defensive: never let a single edge crash the engine.
            pkg.provenance.setdefault("evaluation_errors", []).append(
                {"edge_id": edge.id, "error": str(exc)}
            )
            continue

        # Lag ramp: scale down contribution if turn_index < lag_turns (MVP simplification)
        if edge.lag_turns > 0 and state.turn_index < edge.lag_turns:
            contribution *= (state.turn_index + 1) / max(1, edge.lag_turns + 1)

        _add_target_delta(pkg, edge, contribution, spec.metric_categories)
        causal_links.append(
            CausalLinkActive(
                edge_id=edge.id,
                source=edge.source,
                target=edge.target,
                source_value=source_value,
                contribution=contribution,
                form=fn_spec.form,
            )
        )

    # 5. Spillover for each vectorized metric — counts as edge-derived (subject to cap)
    friction_lookup = build_friction_lookup(spec.blocks_spec)
    for metric_key in state.block_metrics:
        sp_deltas = compute_spillover(state.block_metrics[metric_key], friction_lookup)
        for block, d in sp_deltas.items():
            pkg.add_to_block(metric_key, block, d, source="edge")

    # 6. Top causal links (sort by absolute contribution, keep top 8)
    causal_links.sort(key=lambda c: abs(c.contribution), reverse=True)
    pkg.causal_links_active = causal_links[:8]
    pkg.provenance["edge_count_evaluated"] = len(causal_links)

    return pkg


# ---------------------------------------------------------------------------- support


def _route_external_delta(
    pkg: DeltaPackage,
    metric_key: str,
    delta: float,
    metric_categories: Dict[str, str],
    source: str = "exogenous",
):
    """Route a delta from event/shock/user_input to the right bucket."""
    base, suffix = _split_block_suffix(metric_key)
    cat = metric_categories.get(base, "global")
    if suffix:
        if cat == "vectorized":
            pkg.add_to_block(base, suffix, delta, source=source)
        elif cat == "matrix":
            pkg.add_to_matrix(base, suffix, delta, source=source)
        else:
            pkg.add_to_global(base, delta, source=source)
        return
    if cat == "global":
        pkg.add_to_global(base, delta, source=source)
    elif cat == "vectorized":
        for b in BLOCKS:
            pkg.add_to_block(base, b, delta, source=source)
    elif cat == "matrix":
        pkg.add_to_matrix(base, "total", delta, source=source)


def _compute_activation_value(
    fn_spec: StructuralFunction,
    state: WorldState,
    metric_categories: Dict[str, str],
) -> float:
    """For sigmoid_temporal: resolve activation_metric using activation_block."""
    if fn_spec.form != "sigmoid_temporal":
        return 0.0
    p = fn_spec.parameters
    metric = p.get("activation_metric")
    block = p.get("activation_block")
    if not metric:
        return 0.0
    base, suffix = _split_block_suffix(metric)
    cat = metric_categories.get(base, "global")
    if cat == "global":
        return float(state.global_metrics.get(base, 0.0))
    if cat == "vectorized":
        if suffix is None and isinstance(block, str) and block in BLOCKS:
            return float(state.block_metrics.get(base, {}).get(block, 0.0))
        if isinstance(block, str) and block in {"weighted_mean", "leader", "max", "sum"}:
            return aggregate_blocks(state.block_metrics.get(base, {}), block)
        if suffix in BLOCKS:
            return float(state.block_metrics.get(base, {}).get(suffix, 0.0))
        # default to weighted_mean
        return aggregate_blocks(state.block_metrics.get(base, {}), "weighted_mean")
    return 0.0
