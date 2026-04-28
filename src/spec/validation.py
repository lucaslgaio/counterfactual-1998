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
    validate_aggregation_consistency,
    validate_edge_fields,
    validate_matrix_targeted_scope,
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
    loops_present: Dict[str, bool] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# Central loops that must be present after Rodada 3.
# Each loop is a list of edges (source, target) that should form a closed cycle
# with total positive lag (so the cycle is well-formed in time).
CENTRAL_LOOPS: Dict[str, List[tuple]] = {
    "ai_funding_cycle": [
        ("financial_markets.global_index", "ai_capability.frontier_capability"),
        ("ai_capability.frontier_capability", "financial_markets.global_index"),
        ("financial_markets.systemic_risk", "ai_capability.frontier_capability"),
    ],
    "regulation_concentration": [
        ("tech_industry.bigtech_concentration", "governance.ai_regulation_maturity"),
        ("governance.ai_regulation_maturity", "tech_industry.bigtech_concentration"),
        ("labor_market.automation_exposure", "governance.ai_regulation_maturity"),
        ("governance.ai_regulation_maturity", "financial_markets.systemic_risk"),
    ],
    "trust_disinformation": [
        ("information_ecosystem.disinformation_level", "information_ecosystem.media_trust"),
        ("information_ecosystem.media_trust", "information_ecosystem.disinformation_level"),
        ("ai_capability.population_penetration", "information_ecosystem.disinformation_level"),
        ("governance.ai_regulation_maturity", "information_ecosystem.disinformation_level"),
    ],
}


def validate_central_loops(edges: List[CausalEdge]) -> Dict[str, Dict[str, object]]:
    """Verifies that the 3 central feedback loops are present in the DAG.

    Returns a dict {loop_name: {present: bool, missing: [(src, tgt), ...]}}.
    """
    edge_pairs = {(e.base_source, e.base_target) for e in edges}
    result: Dict[str, Dict[str, object]] = {}
    for loop_name, required_pairs in CENTRAL_LOOPS.items():
        missing = [pair for pair in required_pairs if pair not in edge_pairs]
        result[loop_name] = {
            "present": len(missing) == 0,
            "missing": missing,
            "required_count": len(required_pairs),
            "found_count": len(required_pairs) - len(missing),
        }
    return result


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
    metric_categories: Dict[str, str] = {m["metric_key"]: m["category"] for m in metrics}

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

    agg_errors = validate_aggregation_consistency(edges, metric_categories)
    report.errors.extend(f"[dag] {e}" for e in agg_errors)

    matrix_errors = validate_matrix_targeted_scope(edges, metric_categories)
    report.errors.extend(f"[dag] {e}" for e in matrix_errors)

    fns: List[StructuralFunction] = load_functions(fns_path)
    fn_errors = validate_functions(fns, {e.id for e in edges})
    report.errors.extend(f"[functions] {e}" for e in fn_errors)

    events_spec: EventsSpec = load_events(events_path)
    event_errors = validate_events(events_spec, full_keys)
    report.errors.extend(f"[events] {e}" for e in event_errors)

    # Central loops check (informational — does not fail validation, only warns)
    loops = validate_central_loops(edges)
    for loop_name, info in loops.items():
        report.loops_present[loop_name] = bool(info["present"])
        if not info["present"]:
            missing_str = ", ".join(f"{s}→{t}" for s, t in info["missing"])
            report.warnings.append(
                f"[loops] central loop {loop_name!r} incomplete: missing {missing_str}"
            )

    report.stats["metrics"] = len(metrics)
    report.stats["edges"] = len(edges)
    report.stats["functions"] = len(fns)
    report.stats["events"] = len(events_spec.events)
    report.stats["delta_packages"] = len(events_spec.delta_packages)
    report.stats["composite_factors"] = len(events_spec.composite_factors)
    report.stats["blocks"] = len(blocks_spec.blocks)
    report.stats["spillover_pairs"] = len(blocks_spec.spillover_friction)
    report.stats["central_loops_present"] = sum(1 for v in report.loops_present.values() if v)
    report.stats["central_loops_total"] = len(CENTRAL_LOOPS)
    # Etapa 2 — informational: % of edges that have been methodologically reviewed.
    # Does not block validation; just reports progress.
    validated_count = sum(1 for e in edges if e.validated)
    report.stats["edges_validated"] = validated_count
    report.stats["edges_validated_pct"] = (
        round(100.0 * validated_count / len(edges), 1) if edges else 0.0
    )

    return report
