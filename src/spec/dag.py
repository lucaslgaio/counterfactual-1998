# DRAFT - revisar com humano
"""Loader and validator for spec/causal_dag.json.

Validates:
- All edges reference existing metrics in metric_taxonomy.json
- Acyclicity of the lag-0 sub-DAG (edges with lag_turns == 0 form a DAG)
- Edges with lag_turns >= 1 break cycles when unrolled in time
- Magnitude in {weak, medium, strong}
- Direction in {positive, negative}
- Scope in {within_block, spillover, global}
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

import networkx as nx

VALID_MAGNITUDES = {"weak", "medium", "strong", "negligible"}
VALID_DIRECTIONS = {"positive", "negative"}
VALID_SCOPES = {"within_block", "spillover", "global", "matrix_targeted"}
VALID_AGGREGATIONS = {"leader", "weighted_mean", "max", "sum"}
BLOCK_IDS = {"US", "EU", "CN", "RoW"}


@dataclass
class CausalEdge:
    id: str
    source: str
    target: str
    direction: str
    magnitude: str
    lag_turns: int
    scope: str
    justification_ref: str
    draft: bool = True
    is_self_loop: bool = False
    aggregation: Optional[str] = None
    direction_contested: bool = False

    @property
    def base_source(self) -> str:
        """Returns source metric without block suffix."""
        return _strip_block_suffix(self.source)

    @property
    def base_target(self) -> str:
        """Returns target metric without block suffix."""
        return _strip_block_suffix(self.target)


def _strip_block_suffix(metric_key: str) -> str:
    """Removes a trailing .US/.EU/.CN/.RoW or matrix pair (.A_B) from a metric key.

    >>> _strip_block_suffix("ai_capability.frontier_capability.US")
    'ai_capability.frontier_capability'
    >>> _strip_block_suffix("financial_markets.global_index")
    'financial_markets.global_index'
    >>> _strip_block_suffix("geopolitics.bilateral_tensions.US_CN")
    'geopolitics.bilateral_tensions'
    """
    parts = metric_key.split(".")
    if len(parts) < 2:
        return metric_key
    last = parts[-1]
    if last in BLOCK_IDS:
        return ".".join(parts[:-1])
    if "_" in last:
        a, _, b = last.partition("_")
        if a in BLOCK_IDS and (b in BLOCK_IDS or b == "RoW" or last.startswith("internal_")):
            return ".".join(parts[:-1])
    return metric_key


def load_dag(path: Path) -> List[CausalEdge]:
    """Loads spec/causal_dag.json and returns a list of CausalEdge."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    edges_data = raw.get("edges", [])
    edges: List[CausalEdge] = []
    for e in edges_data:
        edges.append(CausalEdge(
            id=e["id"],
            source=e["source"],
            target=e["target"],
            direction=e["direction"],
            magnitude=e["magnitude"],
            lag_turns=int(e["lag_turns"]),
            scope=e["scope"],
            justification_ref=e["justification_ref"],
            draft=bool(e.get("draft", True)),
            is_self_loop=bool(e.get("is_self_loop", False)),
            aggregation=e.get("aggregation"),
            direction_contested=bool(e.get("direction_contested", False)),
        ))
    return edges


def validate_edge_fields(edges: List[CausalEdge]) -> List[str]:
    """Returns a list of error strings (empty if all valid)."""
    errors: List[str] = []
    seen_ids: Set[str] = set()
    for e in edges:
        if e.id in seen_ids:
            errors.append(f"duplicate edge id: {e.id}")
        seen_ids.add(e.id)
        if e.direction not in VALID_DIRECTIONS:
            errors.append(f"{e.id}: invalid direction {e.direction!r}")
        if e.magnitude not in VALID_MAGNITUDES:
            errors.append(f"{e.id}: invalid magnitude {e.magnitude!r}")
        if e.scope not in VALID_SCOPES:
            errors.append(f"{e.id}: invalid scope {e.scope!r}")
        if e.lag_turns < 0:
            errors.append(f"{e.id}: lag_turns must be >= 0, got {e.lag_turns}")
        if e.aggregation is not None and e.aggregation not in VALID_AGGREGATIONS:
            errors.append(f"{e.id}: invalid aggregation {e.aggregation!r}")
    return errors


def validate_aggregation_consistency(
    edges: List[CausalEdge], metric_categories: dict
) -> List[str]:
    """Checks that every vector→global edge has aggregation defined,
    and that within_block / spillover / matrix_targeted edges DON'T have aggregation.

    metric_categories: {base_metric_key: "vectorized" | "global" | "matrix"}
    """
    errors: List[str] = []
    for e in edges:
        src_cat = metric_categories.get(e.base_source)
        tgt_cat = metric_categories.get(e.base_target)
        if src_cat == "vectorized" and tgt_cat == "global":
            if e.aggregation is None:
                errors.append(
                    f"{e.id}: vector→global edge missing aggregation field "
                    f"({e.source} → {e.target})"
                )
        elif e.aggregation is not None:
            # Allow aggregation on global→global edges (for symmetry/clarity)
            # but not on within_block / spillover / matrix_targeted
            if e.scope in ("within_block", "spillover", "matrix_targeted"):
                if src_cat != "vectorized" or tgt_cat != "global":
                    # aggregation only meaningful for vector→global
                    errors.append(
                        f"{e.id}: aggregation set but edge is not vector→global "
                        f"(scope={e.scope}, src={src_cat}, tgt={tgt_cat})"
                    )
    return errors


def validate_matrix_targeted_scope(
    edges: List[CausalEdge], metric_categories: dict
) -> List[str]:
    """Edges whose target is a matrix metric must have scope='matrix_targeted'."""
    errors: List[str] = []
    for e in edges:
        tgt_cat = metric_categories.get(e.base_target)
        if tgt_cat == "matrix":
            if e.scope != "matrix_targeted":
                errors.append(
                    f"{e.id}: target {e.target!r} is matrix metric "
                    f"but scope is {e.scope!r} (must be 'matrix_targeted')"
                )
        elif e.scope == "matrix_targeted" and tgt_cat != "matrix":
            errors.append(
                f"{e.id}: scope is matrix_targeted but target {e.target!r} "
                f"is not a matrix metric (category={tgt_cat})"
            )
    return errors


def validate_metric_references(edges: List[CausalEdge], known_metric_keys: Set[str]) -> List[str]:
    """Validates that edge source/target reference known metrics (after block-suffix stripping)."""
    errors: List[str] = []
    for e in edges:
        for label, raw in (("source", e.source), ("target", e.target)):
            stripped = _strip_block_suffix(raw)
            if stripped not in known_metric_keys:
                errors.append(f"{e.id}: {label} {raw!r} (stripped: {stripped!r}) not in metric_taxonomy")
    return errors


def validate_acyclicity(edges: List[CausalEdge]) -> List[str]:
    """Validates that lag-0 edges do not form cycles.

    Edges with lag_turns >= 1 are allowed to "close cycles" when unrolled in time
    (they form a DAG when each turn is a separate node).
    """
    errors: List[str] = []
    g = nx.DiGraph()
    for e in edges:
        if e.lag_turns == 0 and not e.is_self_loop:
            g.add_edge(e.base_source, e.base_target, edge_id=e.id)
    try:
        cycles = list(nx.simple_cycles(g))
    except Exception as exc:
        errors.append(f"cycle detection failed: {exc}")
        return errors
    if cycles:
        for cycle in cycles:
            errors.append(f"lag-0 cycle detected: {' -> '.join(cycle)} -> {cycle[0]}")
    return errors


def build_networkx_graph(edges: List[CausalEdge]) -> nx.DiGraph:
    """Builds a NetworkX DiGraph from edges. Useful for stats and rendering."""
    g = nx.DiGraph()
    for e in edges:
        g.add_edge(
            e.base_source,
            e.base_target,
            edge_id=e.id,
            direction=e.direction,
            magnitude=e.magnitude,
            lag_turns=e.lag_turns,
            scope=e.scope,
        )
    return g
