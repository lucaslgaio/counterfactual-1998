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
