# DRAFT - revisar com humano
"""Integrated validator for the spec/ folder.

Runs all validators across the four spec files and returns a structured
report. Used by scripts/validate_spec.py and tests.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from src.spec.blocks import BlocksSpec, load_blocks, validate_blocks
from src.spec.dag import (
    CausalEdge,
    load_dag,
    validate_acyclicity,
    validate_edge_fields,
    validate_metric_references,
)
from src.spec.events import (
    EventsSpec,
    expand_metric_keys,
    load_events,
    validate_events,
)
from src.spec.functions import (
    StructuralFunction,
    load_functions,
    validate_functions,
)


SPEC_DIR_DEFAULT = Path(__file__).parent.parent.parent / "spec"


@dataclass
class ValidationReport:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def load_metric_taxonomy(path: Path) -> List[Dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return raw.get("metrics", [])


def run_full_validation(spec_dir: Path = SPEC_DIR_DEFAULT) -> ValidationReport:
    """Loads all four spec files and runs cross-cutting validations."""
    report = ValidationReport()

    taxonomy_path = spec_dir / "metric_taxonomy.json"
    blocks_path = spec_dir / "geographic_blocks.json"
    dag_path = spec_dir / "causal_dag.json"
    fns_path = spec_dir / "structural_functions.json"
    events_path = spec_dir / "event_variants.json"

    for p in (taxonomy_path, blocks_path, dag_path, fns_path, events_path):
        if not p.exists():
            report.errors.append(f"missing spec file: {p.name}")
            return report

    metrics = load_metric_taxonomy(taxonomy_path)
    base_keys: Set[str] = {m["metric_key"] for m in metrics}
    full_keys: Set[str] = expand_metric_keys(metrics)

    blocks_spec: BlocksSpec = load_blocks(blocks_path)
    block_errors = validate_blocks(blocks_spec)
    report.errors.extend(f"[blocks] {e}" for e in block_errors)

    edges: List[CausalEdge] = load_dag(dag_path)
    field_errors = validate_edge_fields(edges)
    report.errors.extend(f"[dag] {e}" for e in field_errors)

    ref_errors = validate_metric_references(edges, base_keys)
    report.errors.extend(f"[dag] {e}" for e in ref_errors)

    cycle_errors = validate_acyclicity(edges)
    report.errors.extend(f"[dag] {e}" for e in cycle_errors)

    fns: List[StructuralFunction] = load_functions(fns_path)
    fn_errors = validate_functions(fns, {e.id for e in edges})
    report.errors.extend(f"[functions] {e}" for e in fn_errors)

    events_spec: EventsSpec = load_events(events_path)
    event_errors = validate_events(events_spec, full_keys)
    report.errors.extend(f"[events] {e}" for e in event_errors)

    report.stats["metrics"] = len(metrics)
    report.stats["edges"] = len(edges)
    report.stats["functions"] = len(fns)
    report.stats["events"] = len(events_spec.events)
    report.stats["delta_packages"] = len(events_spec.delta_packages)
    report.stats["composite_factors"] = len(events_spec.composite_factors)
    report.stats["blocks"] = len(blocks_spec.blocks)
    report.stats["spillover_pairs"] = len(blocks_spec.spillover_friction)

    return report
