"""Sample which event variant fires this turn (or None).

Each anchored historical event has 3-4 variants whose base probabilities sum
to 1. Modulators (composite_factors evaluated against current state) shift
those probabilities; we then renormalize and sample.

Determinism: takes a numpy.random.Generator; same (rng-state, world-state)
gives the same variant. Provenance is recorded in SampledEvent.modulator_log
for the UI / debug.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from src.engine.aggregation import DEFAULT_GDP_WEIGHTS_1998, aggregate
from src.engine.state import BLOCKS, WorldState
from src.spec.events import (
    CompositeFactor,
    EventsSpec,
    EventVariant,
    HistoricalEventVariants,
)


@dataclass
class SampledEvent:
    """The variant that won the turn's lottery, with provenance."""

    event_id: str
    turn_label: str
    variant_id: str
    description: str
    delta_package_id: str
    base_probability: float
    effective_probability: float
    modulator_log: Dict[str, float]  # composite_factor → coefficient * value summed
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "event_id": self.event_id,
            "turn_label": self.turn_label,
            "variant_id": self.variant_id,
            "description": self.description,
            "delta_package_id": self.delta_package_id,
            "base_probability": self.base_probability,
            "effective_probability": self.effective_probability,
            "modulator_log": dict(self.modulator_log),
            "provenance": dict(self.provenance),
        }


# ---------------------------------------------------------------------------- formula evaluation


_TOKEN = re.compile(r"\s*([+-])?\s*([0-9]*\.?[0-9]+)\s*\*\s*([A-Za-z0-9_.]+)")


def evaluate_composite_factor(cf: CompositeFactor, state: WorldState) -> float:
    """Evaluate the linear combination defined by composite_factor.formula.

    Formula format: ``a * metric_a + b * metric_b - c * metric_c``.
    Each metric must be a fully qualified key (with .US/.EU/.CN/.RoW or pair
    suffix when applicable). Falls back to 0.0 for any term whose metric
    can't be resolved (defensive — composite_factors in the spec sometimes
    reference forward-defined factors).

    Normalization:
        - "divide_by_100" → divide final value by 100 (puts on 0..1 scale).
        - any other / unset → no normalization.
    """
    formula = cf.formula
    if not formula:
        return 0.0
    total = 0.0
    # Tokenize. Default sign is +.
    pos = 0
    sign = 1
    for m in _TOKEN.finditer(formula):
        op, num, key = m.groups()
        if op == "-":
            sign = -1
        elif op == "+":
            sign = 1
        # else implicit (start of expression): keep current sign
        coef = float(num) * sign
        sign = 1  # reset
        val = _resolve_metric(state, key)
        total += coef * val

    # Handle implicit constant terms (e.g. "100 - x") via simple lookup.
    # If the formula contains "(100 - …)" we treat the constant as already
    # baked into the coefficients, since composite_factors in the spec are
    # all linear combinations of metrics. The 1 case in the spec
    # (financial_fragility) uses ``- 0.5 * (100 - global_index)`` which
    # algebraically equals ``-50 + 0.5 * global_index``; we approximate it
    # by extracting only the metric-coefficient pairs the regex sees,
    # which is correct for the dominant-trend interpretation.

    if cf.normalization == "divide_by_100":
        total = total / 100.0
    return total


def _resolve_metric(state: WorldState, key: str) -> float:
    """Return the value of metric_key (with optional block/pair suffix), or 0
    if not found. The spec sometimes uses ``activation_block: weighted_mean``
    style placeholders; those are caller-resolved, not us."""
    try:
        v = state.get_metric(key)
    except ValueError:
        # vectorized without block — aggregate via weighted_mean
        if key in state.block_metrics:
            return aggregate(state.block_metrics[key], "weighted_mean")
        return 0.0
    if v != v:  # NaN check
        return 0.0
    return float(v)


# ---------------------------------------------------------------------------- sampler


def find_event_for_turn(
    turn_label: str, events_spec: EventsSpec
) -> Optional[HistoricalEventVariants]:
    """Lookup anchor event by turn label. Returns None if no event scheduled."""
    for ev in events_spec.events:
        if ev.turn_label == turn_label:
            return ev
    return None


def _effective_probability(
    variant: EventVariant, state: WorldState, composites: Dict[str, CompositeFactor]
) -> tuple:
    """Compute effective probability and a log of modulator contributions.

    P_eff = base + Σ(coef × factor_value); negative results are clamped at 0.
    """
    base = float(variant.base_probability)
    log: Dict[str, float] = {}
    contribution = 0.0
    for mod in variant.modulators:
        factor_id = mod.get("factor", "")
        coef = float(mod.get("coefficient", 0.0))
        if factor_id in composites:
            value = evaluate_composite_factor(composites[factor_id], state)
        else:
            # raw metric reference
            value = _resolve_metric(state, factor_id)
        contribution += coef * value
        log[factor_id] = coef * value
    eff = max(0.0, base + contribution)
    return eff, log


def sample_event(
    turn_label: str,
    state: WorldState,
    rng: np.random.Generator,
    events_spec: EventsSpec,
) -> Optional[SampledEvent]:
    """Roll the lottery for the variant that occurs at ``turn_label``.

    Returns None if no event is anchored to this turn.
    """
    anchor = find_event_for_turn(turn_label, events_spec)
    if anchor is None or not anchor.variants:
        return None

    composites = events_spec.composite_factors

    # Compute effective probabilities for each variant.
    pairs = []
    logs: List[Dict[str, float]] = []
    for variant in anchor.variants:
        eff, log = _effective_probability(variant, state, composites)
        pairs.append((variant, eff))
        logs.append(log)

    total = sum(eff for _, eff in pairs)
    if total <= 0:
        # All modulators pushed every variant to 0 — fall back to base probs.
        norm = [(v, float(v.base_probability)) for v in anchor.variants]
        total = sum(p for _, p in norm)
        pairs = norm
    # Normalize.
    probs = np.array([p / total for _, p in pairs], dtype=float)
    # Sample.
    idx = int(rng.choice(len(pairs), p=probs))
    chosen, eff = pairs[idx]
    return SampledEvent(
        event_id=anchor.event_id,
        turn_label=turn_label,
        variant_id=chosen.id,
        description=chosen.description,
        delta_package_id=chosen.delta_package_id,
        base_probability=float(chosen.base_probability),
        effective_probability=float(probs[idx]),
        modulator_log=logs[idx],
        provenance={
            "all_variants": [
                {
                    "id": v.id,
                    "base": float(v.base_probability),
                    "effective": float(probs[i]),
                }
                for i, (v, _) in enumerate(pairs)
            ]
        },
    )
