"""Load historical time series from data/historical/ CSVs.

Each CSV must follow this schema (see data/historical/README.md):

    turn_label,turn_index,value,metric_key,block,confidence,source_url,notes

Files whose name contains ``PLACEHOLDER`` are skipped with a warning so the
calibration runs against real-data series only.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "historical"

logger = logging.getLogger(__name__)


@dataclass
class HistoricalSeries:
    """A single time series aligned to the engine's 58 turns.

    Attributes
    ----------
    metric_key : the spec metric_key (e.g. ``health.life_expectancy``).
    block : ``"US"``/``"EU"``/``"CN"``/``"RoW"`` for vectorized series; None for global.
    turn_labels : the 58 turn labels in order. Always present in full.
    values : np.ndarray of shape (58,). NaN where the series didn't have data.
    confidence : 0..1 — caller's signal of how much to trust the values.
    source : URL or descriptor of where the data comes from.
    notes : free-text annotations.
    """

    metric_key: str
    block: Optional[str]
    turn_labels: List[str]
    values: np.ndarray
    confidence: float
    source: str
    notes: str = ""

    def is_global(self) -> bool:
        return self.block is None or self.block == ""

    def has_data(self) -> bool:
        """True if at least one non-NaN value is present."""
        return not bool(np.all(np.isnan(self.values)))

    @property
    def series_id(self) -> str:
        """Stable id used as a dict key in calibration: metric_key[+block]."""
        if self.is_global():
            return self.metric_key
        return f"{self.metric_key}.{self.block}"


# ---------------------------------------------------------------------------- loader


def load_csv_series(csv_path: Path, total_turns: int = 58) -> Optional[HistoricalSeries]:
    """Load one CSV file. Returns None for PLACEHOLDER files."""
    if "PLACEHOLDER" in csv_path.name.upper():
        logger.info("skipping PLACEHOLDER file: %s", csv_path.name)
        return None

    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        return None

    metric_key = rows[0].get("metric_key", "").strip()
    block = rows[0].get("block", "").strip() or None
    source = rows[0].get("source_url", "").strip()
    notes = rows[0].get("notes", "").strip()
    try:
        confidence = float(rows[0].get("confidence", "0.5"))
    except ValueError:
        confidence = 0.5

    # Build value array aligned to turn_labels.
    values = np.full(total_turns, np.nan, dtype=float)
    turn_labels: List[str] = []

    by_idx: Dict[int, float] = {}
    for r in rows:
        try:
            idx = int(r["turn_index"])
        except (KeyError, ValueError):
            continue
        if 0 <= idx < total_turns:
            try:
                v = float(r["value"]) if r.get("value", "").strip() else np.nan
            except ValueError:
                v = np.nan
            by_idx[idx] = v

    # Generate canonical labels and fill values.
    for year in range(1998, 2027):
        for sem in (1, 2):
            turn_labels.append(f"{year}-S{sem}")
    for idx, v in by_idx.items():
        if 0 <= idx < total_turns:
            values[idx] = v

    return HistoricalSeries(
        metric_key=metric_key,
        block=block,
        turn_labels=turn_labels,
        values=values,
        confidence=confidence,
        source=source,
        notes=notes,
    )


def load_all_series(data_dir: Path = DEFAULT_DATA_DIR) -> Dict[str, HistoricalSeries]:
    """Load every non-PLACEHOLDER CSV in ``data_dir``.

    Returns dict keyed by ``series_id`` (metric_key for global, metric_key.BLOCK
    for per-block). Skips PLACEHOLDER files with a log warning.
    """
    out: Dict[str, HistoricalSeries] = {}
    for csv_path in sorted(data_dir.glob("*.csv")):
        s = load_csv_series(csv_path)
        if s is None:
            continue
        if not s.has_data():
            logger.warning("series %s has no usable data points; skipping", csv_path.name)
            continue
        out[s.series_id] = s
    return out


def coverage_report(series_dict: Dict[str, HistoricalSeries]) -> Dict[str, Dict[str, int]]:
    """Per-series count of valid (non-NaN) data points and confidence."""
    return {
        sid: {
            "non_nan_points": int(np.sum(~np.isnan(s.values))),
            "confidence": float(s.confidence),
            "first_turn": int(np.argmax(~np.isnan(s.values))) if s.has_data() else -1,
        }
        for sid, s in series_dict.items()
    }
