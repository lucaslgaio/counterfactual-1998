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
    validate_aggregation_consistency,
    validate_edge_fields,
    validate_matrix_targeted_scope,
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
    # Etapa 1.5 expanded the DAG to ~130 edges. Cap is generous to allow further additions.
    assert len(edges) <= 200, "expected at most 200 edges (sanity bound)"


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


# Etapa 1.5 — novos validadores


def _categories_from_real_taxonomy() -> dict:
    raw = json.loads((SPEC_DIR / "metric_taxonomy.json").read_text(encoding="utf-8"))
    return {m["metric_key"]: m["category"] for m in raw["metrics"]}


def test_real_dag_passes_aggregation_consistency():
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    cats = _categories_from_real_taxonomy()
    errors = validate_aggregation_consistency(edges, cats)
    assert not errors, f"aggregation errors: {errors}"


def test_real_dag_passes_matrix_targeted_scope():
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    cats = _categories_from_real_taxonomy()
    errors = validate_matrix_targeted_scope(edges, cats)
    assert not errors, f"matrix_targeted errors: {errors}"


def test_aggregation_required_for_vector_to_global():
    bad = [CausalEdge(
        id="e_x", source="ai_capability.frontier_capability",
        target="financial_markets.global_index", direction="positive",
        magnitude="medium", lag_turns=1, scope="global",
        justification_ref="x", aggregation=None,
    )]
    cats = {
        "ai_capability.frontier_capability": "vectorized",
        "financial_markets.global_index": "global",
    }
    errors = validate_aggregation_consistency(bad, cats)
    assert any("missing aggregation" in e for e in errors)


def test_aggregation_invalid_value_caught():
    bad = [CausalEdge(
        id="e_x", source="a.b", target="c.d", direction="positive",
        magnitude="medium", lag_turns=1, scope="global",
        justification_ref="x", aggregation="invalid_agg",
    )]
    errors = validate_edge_fields(bad)
    assert any("invalid aggregation" in e for e in errors)


def test_matrix_targeted_required_when_target_is_matrix():
    bad = [CausalEdge(
        id="e_x", source="ai_capability.frontier_capability",
        target="geopolitics.bilateral_tensions", direction="positive",
        magnitude="medium", lag_turns=1, scope="global",
        justification_ref="x",
    )]
    cats = {
        "ai_capability.frontier_capability": "vectorized",
        "geopolitics.bilateral_tensions": "matrix",
    }
    errors = validate_matrix_targeted_scope(bad, cats)
    assert any("must be 'matrix_targeted'" in e for e in errors)


def test_matrix_targeted_rejected_when_target_not_matrix():
    bad = [CausalEdge(
        id="e_x", source="a.b", target="financial_markets.global_index",
        direction="positive", magnitude="medium", lag_turns=1,
        scope="matrix_targeted", justification_ref="x",
    )]
    cats = {
        "a.b": "vectorized",
        "financial_markets.global_index": "global",
    }
    errors = validate_matrix_targeted_scope(bad, cats)
    assert any("not a matrix metric" in e for e in errors)


def test_negligible_magnitude_accepted():
    edge = CausalEdge(
        id="e_x", source="a.b", target="c.d", direction="positive",
        magnitude="negligible", lag_turns=1, scope="global",
        justification_ref="x",
    )
    errors = validate_edge_fields([edge])
    assert not errors


def test_direction_contested_field_loaded():
    """Edges with direction_contested=true should round-trip from JSON."""
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    contested = [e for e in edges if e.direction_contested]
    assert len(contested) >= 1, "expected at least one direction_contested edge after Rodada 1"


# Etapa 2 — methodological review schema


def test_validated_field_invariants():
    """Etapa 2 invariants: validated=true edges must have non-null confidence
    and non-null notes; validated=false edges must have null both."""
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    for e in edges:
        if e.validated:
            assert e.validation_confidence in {"high", "medium", "low"}, (
                f"{e.id}: validated=true requires confidence in high/medium/low, "
                f"got {e.validation_confidence!r}"
            )
            assert e.validation_notes is not None and e.validation_notes != "", (
                f"{e.id}: validated=true requires non-empty validation_notes"
            )
        else:
            assert e.validation_confidence is None, (
                f"{e.id}: validated=false but confidence is {e.validation_confidence!r}"
            )
            assert e.validation_notes is None, (
                f"{e.id}: validated=false but validation_notes is set"
            )


def test_validated_field_round_trips_when_true():
    """A CausalEdge with validated=true and notes should serialize correctly."""
    edge = CausalEdge(
        id="e_x", source="a.b", target="c.d", direction="positive",
        magnitude="medium", lag_turns=2, scope="global",
        justification_ref="x", validated=True,
        validation_confidence="high",
        validation_notes="Reviewed Lucas+Claude 2026-Q2; refs: Author 2020.",
    )
    assert edge.validated is True
    assert edge.validation_notes is not None
    assert edge.validation_confidence == "high"
    errors = validate_edge_fields([edge])
    assert not errors


def test_validation_confidence_accepts_high_medium_low():
    """validation_confidence should accept high, medium, low or None."""
    for level in ("high", "medium", "low"):
        edge = CausalEdge(
            id="e_x", source="a.b", target="c.d", direction="positive",
            magnitude="medium", lag_turns=2, scope="global",
            justification_ref="x", validated=True,
            validation_confidence=level,
            validation_notes="ok",
        )
        errors = validate_edge_fields([edge])
        assert not errors, f"level={level} should be valid: {errors}"


def test_validation_confidence_rejects_invalid_value():
    """validation_confidence with garbage value should be flagged."""
    edge = CausalEdge(
        id="e_x", source="a.b", target="c.d", direction="positive",
        magnitude="medium", lag_turns=2, scope="global",
        justification_ref="x", validated=True,
        validation_confidence="absolute",
        validation_notes="ok",
    )
    errors = validate_edge_fields([edge])
    assert any("invalid validation_confidence" in e for e in errors)


def test_validated_true_requires_confidence():
    """An edge with validated=true but null confidence should be flagged."""
    edge = CausalEdge(
        id="e_x", source="a.b", target="c.d", direction="positive",
        magnitude="medium", lag_turns=2, scope="global",
        justification_ref="x", validated=True,
        validation_confidence=None,
        validation_notes="missing confidence",
    )
    errors = validate_edge_fields([edge])
    assert any("validated=true but validation_confidence is null" in e for e in errors)


def test_validated_false_allows_null_confidence():
    """An edge with validated=false and null confidence is the default and valid."""
    edge = CausalEdge(
        id="e_x", source="a.b", target="c.d", direction="positive",
        magnitude="medium", lag_turns=2, scope="global",
        justification_ref="x",
    )
    assert edge.validated is False
    assert edge.validation_confidence is None
    errors = validate_edge_fields([edge])
    assert not errors
