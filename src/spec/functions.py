# DRAFT - revisar com humano
"""Loader and validator for spec/structural_functions.json."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

VALID_FORMS = {"linear", "log_linear", "sigmoid", "exponential_decay", "sigmoid_temporal"}

REQUIRED_PARAMS = {
    "sigmoid_temporal": {"alpha_pre", "alpha_post", "activation_metric", "activation_block", "threshold"},
}


@dataclass
class StructuralFunction:
    edge_id: str
    form: str
    parameters: Dict[str, Optional[float]]
    clamp_to_range: bool = True
    draft: bool = True


def load_functions(path: Path) -> List[StructuralFunction]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    fns_data = raw.get("functions", [])
    fns: List[StructuralFunction] = []
    for f in fns_data:
        fns.append(StructuralFunction(
            edge_id=f["edge_id"],
            form=f["form"],
            parameters=f.get("parameters", {}),
            clamp_to_range=bool(f.get("clamp_to_range", True)),
            draft=bool(f.get("draft", True)),
        ))
    return fns


def validate_functions(fns: List[StructuralFunction], known_edge_ids: Set[str]) -> List[str]:
    errors: List[str] = []
    seen = set()
    for f in fns:
        if f.edge_id in seen:
            errors.append(f"duplicate function for edge_id {f.edge_id}")
        seen.add(f.edge_id)
        if f.edge_id not in known_edge_ids:
            errors.append(f"function references unknown edge_id {f.edge_id}")
        if f.form not in VALID_FORMS:
            errors.append(f"{f.edge_id}: invalid form {f.form!r}")
            continue
        required = REQUIRED_PARAMS.get(f.form, set())
        missing = required - set(f.parameters.keys())
        if missing:
            errors.append(
                f"{f.edge_id}: form {f.form!r} missing required parameters: {sorted(missing)}"
            )
    missing_fns = known_edge_ids - seen
    if missing_fns:
        errors.append(
            f"{len(missing_fns)} edges have no structural function: "
            f"{sorted(missing_fns)[:5]}{'...' if len(missing_fns) > 5 else ''}"
        )
    return errors
