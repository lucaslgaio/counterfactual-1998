"""Five structural functions used by the SDM engine.

Each function returns a *delta* to be added to the target metric this turn.
None of them clamps; clamping is the responsibility of clamp.py after all
deltas have been accumulated.

Naming convention follows spec/structural_functions.json:
- linear, log_linear, sigmoid, exponential_decay, sigmoid_temporal

Saturation note (e_131): the publications self-loop will explode in 58 turns
without saturation. Self-loops with a target range R use a multiplicative
saturation factor (1 - target / R_max). Tested explicitly.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


# Default magnitude → alpha mapping. Used when a function doesn't have an
# explicit alpha in spec/structural_functions.json. Calibrated for Etapa 5.
DEFAULT_MAGNITUDE_ALPHA = {
    "weak": 0.1,
    "medium": 0.3,
    "strong": 0.7,
    "negligible": 0.02,
}

# Time step. One turn = one semester (6 months). dt=1.0 means alpha is
# expressed in "per-semester" units.
DT = 1.0


@dataclass
class FunctionContext:
    """Bundle of context passed to evaluators.

    - target_range: (min, max) of the target metric (used for saturation).
    - elapsed_turns: turns since the source metric experienced the change
      that this edge is propagating (relevant for exponential_decay).
    - activation_value: precomputed activation_metric value for sigmoid_temporal
      (after aggregation if vector→global).
    - is_self_loop: when true, sigmoid-style saturation is enforced regardless
      of declared form.
    """

    target_range: Optional[tuple] = None
    elapsed_turns: int = 1
    activation_value: float = 0.0
    is_self_loop: bool = False


# ---------------------------------------------------------------------------- functions


def linear(source_value: float, params: Dict[str, Any], ctx: FunctionContext) -> float:
    """delta = alpha * source_value * dt.

    Note: spec uses absolute source_value (not delta from baseline) because
    parameters are pre-calibrated for that convention. See e.g. e_001 with
    alpha=0.04: a frontier_capability of 92 gives delta=3.68/semester to
    automation_exposure (clamped at upper bound but illustrative).
    """
    alpha = float(params.get("alpha", 0.0) or 0.0)
    return alpha * source_value * DT


def log_linear(source_value: float, params: Dict[str, Any], ctx: FunctionContext) -> float:
    """delta = alpha * log(1 + source_value / beta) * dt.

    Diminishing returns: doubling source produces less than doubling delta.
    """
    alpha = float(params.get("alpha", 0.0) or 0.0)
    beta = float(params.get("beta", 1.0) or 1.0)
    if beta <= 0:
        beta = 1.0
    if source_value < 0:
        source_value = 0.0
    return alpha * math.log1p(source_value / beta) * DT


def sigmoid(source_value: float, params: Dict[str, Any], ctx: FunctionContext) -> float:
    """delta = alpha * (target_max - target_value) * sigmoid(source - midpoint) * dt.

    With saturation. ``alpha`` is the steepness; ``beta`` is the midpoint
    (or saturation_target if midpoint is missing). Implemented as:

        contribution = (1 / (1 + exp(-alpha * (source - midpoint))))
        delta = (target_max - target_current) * contribution * dt * step_scale

    where step_scale=0.05 keeps per-turn delta moderate (the distance to
    saturation is the dominant brake).
    """
    alpha = float(params.get("alpha", 0.05) or 0.05)
    midpoint = float(params.get("midpoint", params.get("beta", 50.0)) or 50.0)
    # Distance to saturation (using upper bound of the target range when known)
    target_max = ctx.target_range[1] if ctx.target_range else 100.0
    target_current = float(params.get("_target_current", 0.0) or 0.0)
    headroom = max(0.0, target_max - target_current)
    s = 1.0 / (1.0 + math.exp(-alpha * (source_value - midpoint)))
    step_scale = float(params.get("step_scale", 0.05) or 0.05)
    return headroom * s * step_scale * DT


def exponential_decay(
    source_value: float, params: Dict[str, Any], ctx: FunctionContext
) -> float:
    """delta = alpha * source_value * exp(-elapsed / beta) * dt.

    Effect that fades over time since the source change.
    """
    alpha = float(params.get("alpha", 0.0) or 0.0)
    beta = float(params.get("beta", 1.0) or 1.0)
    if beta <= 0:
        beta = 1.0
    return alpha * source_value * math.exp(-ctx.elapsed_turns / beta) * DT


def sigmoid_temporal(
    source_value: float, params: Dict[str, Any], ctx: FunctionContext
) -> float:
    """Two-regime linear: alpha_pre before activation_value crosses threshold,
    alpha_post after. Used for edges whose dose-response changed historically
    (e.g. disinformation→democracy after 2016).
    """
    threshold = float(params.get("threshold", 0.0) or 0.0)
    if ctx.activation_value >= threshold:
        alpha = float(params.get("alpha_post", 0.0) or 0.0)
    else:
        alpha = float(params.get("alpha_pre", 0.0) or 0.0)
    return alpha * source_value * DT


# Lookup table
FORMS: Dict[str, Callable[[float, Dict[str, Any], FunctionContext], float]] = {
    "linear": linear,
    "log_linear": log_linear,
    "sigmoid": sigmoid,
    "exponential_decay": exponential_decay,
    "sigmoid_temporal": sigmoid_temporal,
}


# ---------------------------------------------------------------------------- evaluator


def evaluate(
    form: str,
    source_value: float,
    target_value: float,
    params: Dict[str, Any],
    ctx: Optional[FunctionContext] = None,
) -> float:
    """Dispatch by form name. Applies self-loop saturation universally.

    Self-loops (e.g. e_131 publications, e_121 democracy, e_074 penetration)
    must NEVER explode. We multiply the form's delta by a saturation factor
    ``(1 - target / target_max)`` so growth slows as target approaches its
    ceiling. This is the critical invariant to keep the engine bounded.
    """
    if ctx is None:
        ctx = FunctionContext()
    fn = FORMS.get(form)
    if fn is None:
        raise ValueError(
            f"unknown structural form {form!r}; valid: {sorted(FORMS)}"
        )
    # sigmoid form needs target_current to compute headroom
    if form == "sigmoid":
        params = {**params, "_target_current": target_value}
    delta = fn(source_value, params, ctx)
    if ctx.is_self_loop:
        delta = _apply_saturation(delta, target_value, ctx)
    return delta


def _apply_saturation(delta: float, target_value: float, ctx: FunctionContext) -> float:
    """Multiplicative saturation factor for self-loops.

    Uses the target range from ctx if available; otherwise assumes the metric
    is unbounded and falls back to a soft-cap at 5x the current value
    (per-turn growth ceiling) to prevent explosion. This is the invariant
    that keeps publications_index stable in the smoke test.
    """
    if delta <= 0:
        return delta  # decay self-loops don't need saturation
    if ctx.target_range is not None:
        lo, hi = ctx.target_range
        # Saturation factor: 1 when target=lo, 0 when target=hi.
        if hi > lo:
            sat = max(0.0, 1.0 - (target_value - lo) / (hi - lo))
            return delta * sat
    # Soft cap when no range: limit growth to 5%/turn
    if target_value > 0:
        cap = 0.05 * target_value
        return min(delta, cap)
    return delta
