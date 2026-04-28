"""Tests for src/spec/functions.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.spec.dag import load_dag
from src.spec.functions import (
    StructuralFunction,
    load_functions,
    validate_functions,
)

SPEC_DIR = Path(__file__).parent.parent.parent / "spec"


def test_load_real_functions():
    fns = load_functions(SPEC_DIR / "structural_functions.json")
    assert len(fns) >= 60, "expected functions for at least 60 edges"


def test_real_functions_validate():
    fns = load_functions(SPEC_DIR / "structural_functions.json")
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    edge_ids = {e.id for e in edges}
    errors = validate_functions(fns, edge_ids)
    assert not errors, f"validation failed: {errors}"


def test_invalid_form_caught():
    bad = [StructuralFunction(edge_id="e_001", form="quadratic", parameters={})]
    errors = validate_functions(bad, {"e_001"})
    assert any("invalid form" in e for e in errors)


def test_unknown_edge_id_caught():
    bad = [StructuralFunction(edge_id="e_999", form="linear", parameters={})]
    errors = validate_functions(bad, {"e_001"})
    assert any("unknown edge_id" in e for e in errors)


def test_missing_function_for_edge_caught():
    fns = [StructuralFunction(edge_id="e_001", form="linear", parameters={})]
    errors = validate_functions(fns, {"e_001", "e_002"})
    assert any("have no structural function" in e for e in errors)


def test_duplicate_function_caught():
    fns = [
        StructuralFunction(edge_id="e_001", form="linear", parameters={}),
        StructuralFunction(edge_id="e_001", form="sigmoid", parameters={}),
    ]
    errors = validate_functions(fns, {"e_001"})
    assert any("duplicate function" in e for e in errors)


# Etapa 1.5 — sigmoid_temporal


def test_sigmoid_temporal_form_accepted():
    fn = StructuralFunction(
        edge_id="e_024", form="sigmoid_temporal",
        parameters={
            "alpha_pre": 0.02, "alpha_post": 0.08,
            "activation_metric": "ai_capability.population_penetration",
            "activation_block": "weighted_mean", "threshold": 30,
        },
    )
    errors = validate_functions([fn], {"e_024"})
    assert not errors


def test_sigmoid_temporal_missing_params_caught():
    fn = StructuralFunction(
        edge_id="e_024", form="sigmoid_temporal",
        parameters={"alpha_pre": 0.02},  # missing alpha_post, activation_*, threshold
    )
    errors = validate_functions([fn], {"e_024"})
    assert any("missing required parameters" in e for e in errors)


def test_real_sigmoid_temporal_edges_have_all_params():
    """Edges e_024, e_063, e_064 should be sigmoid_temporal after Rodada 1."""
    fns = load_functions(SPEC_DIR / "structural_functions.json")
    by_id = {f.edge_id: f for f in fns}
    for eid in ("e_024", "e_063", "e_064"):
        f = by_id[eid]
        assert f.form == "sigmoid_temporal", f"{eid} should be sigmoid_temporal, got {f.form}"
        for param in ("alpha_pre", "alpha_post", "activation_metric", "activation_block", "threshold"):
            assert param in f.parameters, f"{eid} missing {param}"
