"""Define which parameters are calibrated and what ranges they may take.

Selection criteria:
1. Edge magnitude is medium or strong (weak edges aren't worth the effort).
2. Edge structural form has at least one numerical parameter (not 'bypass').
3. The edge's target has historical data (otherwise we can't evaluate fit).

Range determined by the edge's ``validation_confidence`` (Etapa 2):
- high: ±25% of the spec's initial alpha (literature constrains us)
- medium: ±60%
- low: ±100% (can flip sign for weak edges only)
- None (unvalidated): ±80%
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from src.engine.delta_computer import SpecBundle


# Default magnitude→alpha used when spec doesn't specify (kept consistent with engine).
DEFAULT_MAGNITUDE_ALPHA = {
    "weak": 0.1,
    "medium": 0.3,
    "strong": 0.7,
    "negligible": 0.02,
}

CONFIDENCE_RANGE_FACTOR = {
    "high": 0.25,
    "medium": 0.60,
    "low": 1.00,
    None: 0.80,  # unvalidated
}

# Parameter names per form that we calibrate. ``alpha_pre``/``alpha_post`` only
# for sigmoid_temporal; ``threshold`` is too discrete to optimize cleanly.
CALIBRATABLE_PARAMS_BY_FORM = {
    "linear": {"alpha"},
    "log_linear": {"alpha", "beta"},
    "sigmoid": {"alpha"},
    "exponential_decay": {"alpha", "beta"},
    "sigmoid_temporal": {"alpha_pre", "alpha_post"},
}


@dataclass
class CalibratableParameter:
    """One scalar to optimize."""

    edge_id: str
    parameter_name: str  # "alpha", "beta", "alpha_pre", "alpha_post"
    initial_value: float
    range_min: float
    range_max: float
    confidence: Optional[str]  # "high"/"medium"/"low" or None
    is_high_confidence: bool

    @property
    def key(self) -> str:
        return f"{self.edge_id}:{self.parameter_name}"


def _confidence_factor(confidence: Optional[str]) -> float:
    return CONFIDENCE_RANGE_FACTOR.get(confidence, CONFIDENCE_RANGE_FACTOR[None])


def _initial_alpha_for_edge(spec: SpecBundle, edge_id: str, parameter_name: str) -> float:
    """Pull the initial value for one parameter from spec, with fallbacks."""
    fn = spec.functions.get(edge_id)
    if fn is None:
        return 0.0
    p = fn.parameters or {}
    if parameter_name in p and p[parameter_name] is not None:
        return float(p[parameter_name])
    # Fallback: magnitude-based default for alpha-style params.
    edge = next((e for e in spec.edges if e.id == edge_id), None)
    if edge is None:
        return 0.0
    if parameter_name.startswith("alpha"):
        return float(DEFAULT_MAGNITUDE_ALPHA.get(edge.magnitude, 0.1))
    return 0.0


def _range_for_param(initial: float, confidence: Optional[str], allow_sign_flip: bool) -> tuple:
    """Compute (lo, hi) for a parameter."""
    factor = _confidence_factor(confidence)
    width = max(0.001, abs(initial) * factor)
    lo = initial - width
    hi = initial + width
    if not allow_sign_flip:
        # If initial is positive, lo can't go below 0 (sign preservation).
        # If initial is negative, hi can't go above 0.
        if initial > 0:
            lo = max(lo, initial * 0.05)  # don't let it fully zero out
        elif initial < 0:
            hi = min(hi, initial * 0.05)
    return float(lo), float(hi)


def build_parameter_space(
    spec: SpecBundle,
    target_metrics_with_data: Optional[Set[str]] = None,
    calibrate_only_validated: bool = False,
) -> List[CalibratableParameter]:
    """Walk the DAG and build the list of calibratable parameters.

    Parameters
    ----------
    spec : the SpecBundle assembled by build_spec_bundle().
    target_metrics_with_data : optional whitelist of metric_keys (without block
        suffix) for which historical data exists. Edges whose target is NOT in
        this set are skipped (we can't evaluate fit). If None, every edge with
        the right magnitude + form is included.
    calibrate_only_validated : if True, only edges with validated=True are
        included. False by default — we want to try fitting unvalidated edges
        too, with wider ranges.
    """
    out: List[CalibratableParameter] = []
    for edge in spec.edges:
        if edge.magnitude not in {"medium", "strong"}:
            continue
        if calibrate_only_validated and not getattr(edge, "validated", False):
            continue
        fn = spec.functions.get(edge.id)
        if fn is None:
            continue
        param_names = CALIBRATABLE_PARAMS_BY_FORM.get(fn.form, set())
        if not param_names:
            continue

        # Filter by data availability if a whitelist was provided.
        if target_metrics_with_data is not None:
            tgt_base = _strip_block(edge.target)
            if tgt_base not in target_metrics_with_data:
                continue

        confidence = getattr(edge, "validation_confidence", None)
        is_high_conf = confidence == "high"
        # Allow sign flip only for low-confidence weak edges (can't really happen
        # since we filtered weak out — keep guard for future-proofing).
        allow_sign_flip = (confidence == "low") and (edge.magnitude == "weak")

        for pname in sorted(param_names):
            initial = _initial_alpha_for_edge(spec, edge.id, pname)
            if initial == 0.0 and pname.startswith("alpha"):
                # Skip dead alphas (no signal).
                continue
            lo, hi = _range_for_param(initial, confidence, allow_sign_flip)
            out.append(
                CalibratableParameter(
                    edge_id=edge.id,
                    parameter_name=pname,
                    initial_value=initial,
                    range_min=lo,
                    range_max=hi,
                    confidence=confidence,
                    is_high_confidence=is_high_conf,
                )
            )
    return out


def apply_parameters_to_spec(
    spec: SpecBundle,
    parameter_space: List[CalibratableParameter],
    alpha_vector,
) -> SpecBundle:
    """Return a new SpecBundle whose ``functions`` use the provided parameter
    values. The original spec is not mutated.
    """
    new_functions = {eid: _copy_function(fn) for eid, fn in spec.functions.items()}
    for p, v in zip(parameter_space, alpha_vector):
        if p.edge_id not in new_functions:
            continue
        params = dict(new_functions[p.edge_id].parameters or {})
        params[p.parameter_name] = float(v)
        new_functions[p.edge_id].parameters = params
    return SpecBundle(
        edges=spec.edges,
        functions=new_functions,
        metric_categories=spec.metric_categories,
        metric_ranges=spec.metric_ranges,
        blocks_spec=spec.blocks_spec,
        events_spec=spec.events_spec,
    )


def _copy_function(fn):
    """Shallow copy of a StructuralFunction so we can swap parameters safely."""
    from src.spec.functions import StructuralFunction

    return StructuralFunction(
        edge_id=fn.edge_id,
        form=fn.form,
        parameters=dict(fn.parameters or {}),
        clamp_to_range=fn.clamp_to_range,
        draft=fn.draft,
    )


def _strip_block(metric_key: str) -> str:
    """Drop a trailing .US/.EU/.CN/.RoW or matrix pair from a metric key."""
    parts = metric_key.split(".")
    if len(parts) < 2:
        return metric_key
    last = parts[-1]
    if last in {"US", "EU", "CN", "RoW"}:
        return ".".join(parts[:-1])
    if "_" in last:
        a, _, b = last.partition("_")
        if a in {"US", "EU", "CN", "RoW"} and (
            b in {"US", "EU", "CN", "RoW"} or last.startswith("internal_")
        ):
            return ".".join(parts[:-1])
    return metric_key
