"""Range enforcement: keep every metric within its declared [min, max].

Clamping happens after all deltas have been accumulated for the turn.
Returns a new WorldState; never mutates.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from src.engine.state import WorldState

SPEC_DIR_DEFAULT = Path(__file__).parent.parent.parent / "spec"


@dataclass(frozen=True)
class MetricRanges:
    """Map of metric_key → (min, max), loaded from metric_taxonomy.json."""

    ranges: Dict[str, Tuple[float, float]]

    def get(self, metric_key: str) -> Tuple[float, float]:
        return self.ranges.get(metric_key, (float("-inf"), float("inf")))


def load_metric_ranges(spec_dir: Path = SPEC_DIR_DEFAULT) -> MetricRanges:
    tax = json.loads((spec_dir / "metric_taxonomy.json").read_text(encoding="utf-8"))
    ranges = {}
    for m in tax["metrics"]:
        lo, hi = m["range"]
        ranges[m["metric_key"]] = (float(lo), float(hi))
    return MetricRanges(ranges=ranges)


def _clamp_value(v: float, lo: float, hi: float) -> float:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def clamp_state(state: WorldState, ranges: MetricRanges) -> WorldState:
    """Return a new WorldState with every metric clamped to its range."""
    new_global = {
        k: _clamp_value(v, *ranges.get(k)) for k, v in state.global_metrics.items()
    }
    new_block = {}
    for metric_key, by_block in state.block_metrics.items():
        lo, hi = ranges.get(metric_key)
        new_block[metric_key] = {b: _clamp_value(v, lo, hi) for b, v in by_block.items()}
    new_matrix = {}
    for metric_key, by_pair in state.matrix_metrics.items():
        lo, hi = ranges.get(metric_key)
        new_matrix[metric_key] = {p: _clamp_value(v, lo, hi) for p, v in by_pair.items()}
    return WorldState(
        turn_index=state.turn_index,
        turn_label=state.turn_label,
        global_metrics=new_global,
        block_metrics=new_block,
        matrix_metrics=new_matrix,
        metadata=state.metadata,
    )
