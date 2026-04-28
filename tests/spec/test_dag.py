"""Tests for src/spec/dag.py."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.spec.dag import (
    CausalEdge,
    _strip_block_suffix,
    build_networkx_graph,
    load_dag,
    validate_acyclicity,
    validate_edge_fields,
    validate_metric_references,
)

SPEC_DIR = Path(__file__).parent.parent.parent / "spec"


def test_strip_block_suffix_simple():
    assert _strip_block_suffix("ai_capability.frontier_capability") == "ai_capability.frontier_capability"


def test_strip_block_suffix_with_block():
    assert _strip_block_suffix("ai_capability.frontier_capability.US") == "ai_capability.frontier_capability"
    assert _strip_block_suffix("ai_capability.frontier_capability.EU") == "ai_capability.frontier_capability"


def test_strip_block_suffix_with_pair():
    assert _strip_block_suffix("geopolitics.bilateral_tensions.US_CN") == "geopolitics.bilateral_tensions"


def test_load_real_dag():
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    assert len(edges) >= 60, "expected at least 60 edges in DAG"
    assert len(edges) <= 100, "expected at most 100 edges"


def test_real_dag_has_no_lag0_cycles():
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    errors = validate_acyclicity(edges)
    assert not errors, f"DAG has lag-0 cycles: {errors}"


def test_real_dag_field_validation():
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    errors = validate_edge_fields(edges)
    assert not errors, f"DAG has field errors: {errors}"


def test_real_dag_metric_references():
    tax = json.loads((SPEC_DIR / "metric_taxonomy.json").read_text(encoding="utf-8"))
    base_keys = {m["metric_key"] for m in tax["metrics"]}
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    errors = validate_metric_references(edges, base_keys)
    assert not errors, f"DAG references unknown metrics: {errors}"


def test_invalid_direction_caught():
    bad = [CausalEdge(
        id="e_x", source="a.b", target="c.d", direction="sideways",
        magnitude="weak", lag_turns=0, scope="global", justification_ref="x",
    )]
    errors = validate_edge_fields(bad)
    assert any("invalid direction" in e for e in errors)


def test_acyclicity_detects_cycle():
    bad = [
        CausalEdge(id="e_1", source="a.b", target="c.d", direction="positive",
                   magnitude="weak", lag_turns=0, scope="global", justification_ref="x"),
        CausalEdge(id="e_2", source="c.d", target="a.b", direction="positive",
                   magnitude="weak", lag_turns=0, scope="global", justification_ref="y"),
    ]
    errors = validate_acyclicity(bad)
    assert any("cycle" in e for e in errors)


def test_acyclicity_allows_lag_cycles():
    """Edges with lag_turns >= 1 are allowed to close cycles (DAG when unrolled)."""
    edges = [
        CausalEdge(id="e_1", source="a.b", target="c.d", direction="positive",
                   magnitude="weak", lag_turns=2, scope="global", justification_ref="x"),
        CausalEdge(id="e_2", source="c.d", target="a.b", direction="positive",
                   magnitude="weak", lag_turns=2, scope="global", justification_ref="y"),
    ]
    errors = validate_acyclicity(edges)
    assert not errors


def test_metric_references_unknown_caught():
    bad = [CausalEdge(
        id="e_x", source="invalid.metric", target="another.invalid", direction="positive",
        magnitude="weak", lag_turns=0, scope="global", justification_ref="x",
    )]
    errors = validate_metric_references(bad, {"valid.metric"})
    assert len(errors) >= 2


def test_build_networkx_graph_real_dag():
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    g = build_networkx_graph(edges)
    assert g.number_of_nodes() > 0
    assert g.number_of_edges() > 0
