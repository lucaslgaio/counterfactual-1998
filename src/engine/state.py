"""WorldState — frozen snapshot of the counterfactual world at one turn.

Contracts:
- Immutable (frozen dataclass + frozen mappings via tuples + dicts copied on read).
- Round-trippable to JSON.
- Initial state loaded from spec/metric_taxonomy.json + spec/geographic_blocks.json.
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

BLOCKS = ("US", "EU", "CN", "RoW")

SPEC_DIR_DEFAULT = Path(__file__).parent.parent.parent / "spec"


def _generate_turn_labels() -> List[str]:
    """Returns the 58 turn labels: 1998-S1 ... 2026-S2 (semesters)."""
    out = []
    for year in range(1998, 2027):
        for sem in (1, 2):
            out.append(f"{year}-S{sem}")
    return out


TURN_LABELS = _generate_turn_labels()


@dataclass(frozen=True)
class WorldState:
    """Snapshot of the counterfactual world at one turn.

    Frozen for immutability. Use ``with_deltas`` (or other ``with_*``) to derive
    successor states; never mutate fields in place.
    """

    turn_index: int
    turn_label: str
    global_metrics: Dict[str, float]
    block_metrics: Dict[str, Dict[str, float]]  # {metric_key: {block: value}}
    matrix_metrics: Dict[str, Dict[str, float]]  # {metric_key: {pair_or_total: value}}
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ helpers

    def get_metric(self, metric_key: str, block: Optional[str] = None) -> float:
        """Read a metric by key, with optional block/pair specifier embedded
        in the key (e.g. ``ai_capability.frontier_capability.US``).

        Returns NaN if the key is unknown so callers can detect missing data.
        """
        # Strip block/pair suffix if present
        base, suffix = _split_block_suffix(metric_key)
        if base in self.global_metrics and suffix is None:
            return self.global_metrics[base]
        if base in self.block_metrics:
            if suffix is None:
                # vectorized metric without explicit block → return weighted mean
                # via aggregation module to avoid silent errors here.
                raise ValueError(
                    f"vectorized metric {base!r} requested without block suffix; "
                    f"use aggregation.aggregate() or specify .US/.EU/.CN/.RoW"
                )
            return self.block_metrics[base].get(suffix, float("nan"))
        if base in self.matrix_metrics:
            if suffix is None:
                # default to total for active_conflicts; otherwise NaN
                return self.matrix_metrics[base].get("total", float("nan"))
            return self.matrix_metrics[base].get(suffix, float("nan"))
        return float("nan")

    # ------------------------------------------------------------------ construction

    @classmethod
    def from_initial_spec(cls, spec_dir: Path = SPEC_DIR_DEFAULT) -> "WorldState":
        """Build the 1998-S1 baseline from spec/metric_taxonomy.json."""
        tax = json.loads((spec_dir / "metric_taxonomy.json").read_text(encoding="utf-8"))
        global_metrics: Dict[str, float] = {}
        block_metrics: Dict[str, Dict[str, float]] = {}
        matrix_metrics: Dict[str, Dict[str, float]] = {}
        for m in tax["metrics"]:
            key = m["metric_key"]
            cat = m["category"]
            iv = m["initial_values"]
            if cat == "global":
                # initial_values is {"value": x}
                global_metrics[key] = float(iv["value"])
            elif cat == "vectorized":
                block_metrics[key] = {b: float(iv[b]) for b in BLOCKS}
            elif cat == "matrix":
                matrix_metrics[key] = {pair: float(v) for pair, v in iv.items()}
            else:
                raise ValueError(f"unknown category {cat!r} for metric {key!r}")
        return cls(
            turn_index=0,
            turn_label=TURN_LABELS[0],
            global_metrics=global_metrics,
            block_metrics=block_metrics,
            matrix_metrics=matrix_metrics,
            metadata={"source": "from_initial_spec", "spec_dir": str(spec_dir)},
        )

    # ------------------------------------------------------------------ derivation

    def with_advanced_turn(self) -> "WorldState":
        """Return a new state with turn_index/turn_label advanced by one."""
        next_idx = self.turn_index + 1
        if next_idx >= len(TURN_LABELS):
            raise ValueError(f"cannot advance past final turn {TURN_LABELS[-1]}")
        return WorldState(
            turn_index=next_idx,
            turn_label=TURN_LABELS[next_idx],
            global_metrics=copy.deepcopy(self.global_metrics),
            block_metrics=copy.deepcopy(self.block_metrics),
            matrix_metrics=copy.deepcopy(self.matrix_metrics),
            metadata=copy.deepcopy(self.metadata),
        )

    def with_metadata(self, **kwargs) -> "WorldState":
        new_meta = copy.deepcopy(self.metadata)
        new_meta.update(kwargs)
        return WorldState(
            turn_index=self.turn_index,
            turn_label=self.turn_label,
            global_metrics=copy.deepcopy(self.global_metrics),
            block_metrics=copy.deepcopy(self.block_metrics),
            matrix_metrics=copy.deepcopy(self.matrix_metrics),
            metadata=new_meta,
        )

    # ------------------------------------------------------------------ JSON

    def to_json(self) -> dict:
        return {
            "turn_index": self.turn_index,
            "turn_label": self.turn_label,
            "global_metrics": dict(self.global_metrics),
            "block_metrics": {k: dict(v) for k, v in self.block_metrics.items()},
            "matrix_metrics": {k: dict(v) for k, v in self.matrix_metrics.items()},
            "metadata": copy.deepcopy(self.metadata),
        }

    @classmethod
    def from_json(cls, data: dict) -> "WorldState":
        return cls(
            turn_index=int(data["turn_index"]),
            turn_label=str(data["turn_label"]),
            global_metrics={k: float(v) for k, v in data["global_metrics"].items()},
            block_metrics={
                k: {b: float(v) for b, v in subdict.items()}
                for k, subdict in data["block_metrics"].items()
            },
            matrix_metrics={
                k: {pair: float(v) for pair, v in subdict.items()}
                for k, subdict in data["matrix_metrics"].items()
            },
            metadata=data.get("metadata", {}),
        )


# ---------------------------------------------------------------------------- helpers


def _split_block_suffix(metric_key: str):
    """Returns (base_key, suffix) where suffix is the block id, pair, or None."""
    parts = metric_key.split(".")
    if len(parts) < 2:
        return metric_key, None
    last = parts[-1]
    if last in BLOCKS:
        return ".".join(parts[:-1]), last
    if "_" in last:
        a, _, b = last.partition("_")
        if a in BLOCKS and (b in BLOCKS or last.startswith("internal_")):
            return ".".join(parts[:-1]), last
    return metric_key, None
