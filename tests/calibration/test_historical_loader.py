"""Tests for src/calibration/historical_loader.py."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from src.calibration.historical_loader import (
    DEFAULT_DATA_DIR,
    HistoricalSeries,
    coverage_report,
    load_all_series,
    load_csv_series,
)


def _write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            ["turn_label", "turn_index", "value", "metric_key", "block", "confidence", "source_url", "notes"]
        )
        for r in rows:
            w.writerow(r)


def test_load_csv_series_global(tmp_path):
    p = tmp_path / "test_global.csv"
    _write_csv(
        p,
        [
            ("1998-S1", 0, 24.4, "energy_climate.co2_gt_year", "", 0.8, "https://example.com", "test"),
            ("1998-S2", 1, 25.0, "energy_climate.co2_gt_year", "", 0.8, "https://example.com", "test"),
        ],
    )
    s = load_csv_series(p)
    assert s is not None
    assert s.metric_key == "energy_climate.co2_gt_year"
    assert s.is_global()
    assert s.values[0] == 24.4
    assert s.values[1] == 25.0
    assert np.isnan(s.values[2])  # not present


def test_load_csv_series_block(tmp_path):
    p = tmp_path / "test_block.csv"
    _write_csv(
        p,
        [
            ("1998-S1", 0, 0.42, "inequality.gini_intra_block", "US", 0.7, "wid", "ok"),
        ],
    )
    s = load_csv_series(p)
    assert s.block == "US"
    assert s.series_id == "inequality.gini_intra_block.US"


def test_load_csv_series_skips_placeholder(tmp_path):
    p = tmp_path / "thing_PLACEHOLDER.csv"
    _write_csv(p, [("PLACEHOLDER", -1, "", "x", "", 0.0, "url", "todo")])
    s = load_csv_series(p)
    assert s is None


def test_load_all_series_real_data():
    """Smoke test against the actual data/historical/ directory."""
    series = load_all_series()
    # We expect at least the 7 real-ish series
    assert len(series) >= 5, f"only {len(series)} series loaded"
    # PLACEHOLDERs must NOT show up
    for sid in series:
        assert "PLACEHOLDER" not in sid


def test_coverage_report_structure():
    series = load_all_series()
    cov = coverage_report(series)
    for sid, info in cov.items():
        assert info["non_nan_points"] > 0
        assert 0.0 <= info["confidence"] <= 1.0


def test_series_with_all_nans_skipped(tmp_path):
    p = tmp_path / "empty.csv"
    _write_csv(p, [])  # only header
    s = load_csv_series(p)
    # All-empty CSV → returns None
    assert s is None
