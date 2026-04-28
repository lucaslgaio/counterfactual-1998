"""Tests for src/spec/validation.py — integrated validator."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.spec.validation import run_full_validation, ValidationReport

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
