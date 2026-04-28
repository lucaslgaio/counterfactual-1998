"""Tests for src/spec/validation.py — integrated validator."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.spec.dag import load_dag
from src.spec.validation import (
    CENTRAL_LOOPS,
    run_full_validation,
    validate_central_loops,
    ValidationReport,
)

SPEC_DIR = Path(__file__).parent.parent.parent / "spec"


def test_full_validation_on_real_spec():
    report = run_full_validation(SPEC_DIR)
    assert report.ok, f"validation failed with {len(report.errors)} errors: {report.errors[:5]}"


def test_full_validation_returns_stats():
    report = run_full_validation(SPEC_DIR)
    expected_keys = {
        "metrics", "edges", "functions", "events",
        "delta_packages", "composite_factors", "blocks", "spillover_pairs",
    }
    assert expected_keys.issubset(report.stats.keys())
    assert report.stats["metrics"] == 26  # 24 base + mental_wellbeing + gini_between_blocks (Etapa 1.5)
    assert report.stats["events"] == 16
    assert report.stats["edges"] >= 60


def test_full_validation_handles_missing_dir(tmp_path: Path):
    report = run_full_validation(tmp_path)
    assert not report.ok
    assert any("missing spec file" in e for e in report.errors)


def test_validation_report_ok_property():
    report = ValidationReport()
    assert report.ok
    report.errors.append("oops")
    assert not report.ok


# Etapa 1.5 Rodada 3 — central loops


def test_central_loops_defined():
    """The 3 central loops of the project must be defined."""
    assert "ai_funding_cycle" in CENTRAL_LOOPS
    assert "regulation_concentration" in CENTRAL_LOOPS
    assert "trust_disinformation" in CENTRAL_LOOPS


def test_real_dag_has_all_central_loops():
    """After Rodada 3, all 3 central loops should be present in the real DAG."""
    edges = load_dag(SPEC_DIR / "causal_dag.json")
    result = validate_central_loops(edges)
    for loop_name, info in result.items():
        assert info["present"], (
            f"central loop {loop_name} incomplete: missing {info['missing']}"
        )


def test_full_validation_reports_loop_presence():
    report = run_full_validation(SPEC_DIR)
    assert "central_loops_present" in report.stats
    assert "central_loops_total" in report.stats
    # Rodada 3 should have all 3 loops present
    assert report.stats["central_loops_present"] == 3
    assert report.stats["central_loops_total"] == 3
    for loop_name in CENTRAL_LOOPS:
        assert report.loops_present.get(loop_name) is True


# Etapa 2 — methodological review stats


def test_full_validation_reports_validation_progress():
    """run_full_validation should expose Etapa 2 review stats (informational only)."""
    report = run_full_validation(SPEC_DIR)
    assert "edges_validated" in report.stats
    assert "edges_validated_pct" in report.stats
    assert isinstance(report.stats["edges_validated"], int)
    # Currently expected to be 0 (no edges reviewed yet) but the validator
    # only requires the key to be present; we don't assert the value.
    assert report.stats["edges_validated"] >= 0
    assert 0.0 <= report.stats["edges_validated_pct"] <= 100.0


def test_central_loops_detect_missing():
    """If a required edge is missing, the validator should flag it."""
    # Build a small fake DAG with only some of the required edges
    from src.spec.dag import CausalEdge
    edges = [
        CausalEdge(
            id="e_1", source="financial_markets.global_index",
            target="ai_capability.frontier_capability",
            direction="positive", magnitude="medium", lag_turns=4,
            scope="global", justification_ref="x",
        ),
    ]
    result = validate_central_loops(edges)
    assert result["ai_funding_cycle"]["present"] is False
    assert len(result["ai_funding_cycle"]["missing"]) >= 2
