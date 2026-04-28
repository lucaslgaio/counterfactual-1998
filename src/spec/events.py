# DRAFT - revisar com humano
"""Loader and validator for spec/event_variants.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class EventVariant:
    id: str
    description: str
    base_probability: float
    modulators: List[Dict] = field(default_factory=list)
    delta_package_id: str = ""


@dataclass
class HistoricalEventVariants:
    event_id: str
    turn_label: str
    description: str
    variants: List[EventVariant]
    draft: bool = True


@dataclass
class DeltaPackage:
    id: str
    description: str
    deltas: Dict[str, float]
    draft: bool = True


@dataclass
class CompositeFactor:
    id: str
    formula: str
    normalization: str
    draft: bool = True


@dataclass
class EventsSpec:
    events: List[HistoricalEventVariants]
    delta_packages: Dict[str, DeltaPackage]
    composite_factors: Dict[str, CompositeFactor]


def load_events(path: Path) -> EventsSpec:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    events: List[HistoricalEventVariants] = []
    for e in raw.get("events", []):
        variants = [
            EventVariant(
                id=v["id"],
                description=v["description"],
                base_probability=float(v["base_probability"]),
                modulators=v.get("modulators", []),
                delta_package_id=v.get("delta_package_id", ""),
            )
            for v in e.get("variants", [])
        ]
        events.append(HistoricalEventVariants(
            event_id=e["event_id"],
            turn_label=e["turn_label"],
            description=e["description"],
            variants=variants,
            draft=bool(e.get("draft", True)),
        ))

    delta_packages = {
        pkg_id: DeltaPackage(
            id=pkg_id,
            description=pkg.get("description", ""),
            deltas=pkg.get("deltas", {}),
            draft=bool(pkg.get("draft", True)),
        )
        for pkg_id, pkg in raw.get("delta_packages", {}).items()
    }

    composite_factors = {
        cf_id: CompositeFactor(
            id=cf_id,
            formula=cf.get("formula", ""),
            normalization=cf.get("normalization", ""),
            draft=bool(cf.get("draft", True)),
        )
        for cf_id, cf in raw.get("composite_factors", {}).items()
    }

    return EventsSpec(
        events=events,
        delta_packages=delta_packages,
        composite_factors=composite_factors,
    )


def validate_events(spec: EventsSpec, known_metric_keys_with_blocks: Set[str]) -> List[str]:
    errors: List[str] = []
    delta_pkg_ids = set(spec.delta_packages.keys())
    composite_ids = set(spec.composite_factors.keys())

    for ev in spec.events:
        prob_sum = sum(v.base_probability for v in ev.variants)
        if not (0.99 <= prob_sum <= 1.01):
            errors.append(
                f"{ev.event_id}: variant base_probabilities sum to {prob_sum:.3f}, expected 1.0"
            )
        for v in ev.variants:
            if v.delta_package_id and v.delta_package_id not in delta_pkg_ids:
                errors.append(
                    f"{ev.event_id} variant {v.id!r}: unknown delta_package_id {v.delta_package_id!r}"
                )
            for m in v.modulators:
                factor = m.get("factor", "")
                if (
                    factor
                    and factor not in composite_ids
                    and factor not in known_metric_keys_with_blocks
                ):
                    errors.append(
                        f"{ev.event_id} variant {v.id!r}: unknown modulator factor {factor!r}"
                    )

    for pkg_id, pkg in spec.delta_packages.items():
        for metric_key in pkg.deltas:
            if metric_key not in known_metric_keys_with_blocks:
                errors.append(
                    f"delta_package {pkg_id!r}: unknown metric key {metric_key!r}"
                )

    return errors


def expand_metric_keys(taxonomy_metrics: List[Dict]) -> Set[str]:
    """Given the metric_taxonomy entries, returns all valid metric keys
    including block-suffixed versions for vectorized and matrix metrics.
    """
    keys: Set[str] = set()
    for m in taxonomy_metrics:
        key = m["metric_key"]
        category = m["category"]
        keys.add(key)
        if category == "vectorized":
            for block in ("US", "EU", "CN", "RoW"):
                keys.add(f"{key}.{block}")
        elif category == "matrix":
            pairs = m.get("matrix_pairs", [])
            for pair in pairs:
                keys.add(f"{key}.{pair}")
    return keys
