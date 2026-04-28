"""Aggregation rules for vector → global edges.

When an edge has source vectorized and target global, the spec assigns an
aggregation rule (leader / weighted_mean / max / sum). This module is the
single place those rules are evaluated.

GDP shares 1998 are the default weights for ``weighted_mean`` because they
roughly track each block's economic and technological influence; calibration
in Etapa 5 may revise them.
"""
from __future__ import annotations

from typing import Dict, Optional

# GDP shares 1998 from spec/geographic_blocks.json. Sum to 1.0.
DEFAULT_GDP_WEIGHTS_1998 = {
    "US": 0.30,
    "EU": 0.27,
    "CN": 0.07,
    "RoW": 0.36,
}

VALID_RULES = {"leader", "weighted_mean", "max", "sum"}


def aggregate(
    block_values: Dict[str, float],
    rule: str,
    block_weights: Optional[Dict[str, float]] = None,
) -> float:
    """Aggregate a vectorized metric to a single scalar.

    Args:
        block_values: {block_id: value} for US/EU/CN/RoW.
        rule: one of leader / weighted_mean / max / sum.
        block_weights: optional override; defaults to GDP shares 1998.

    Edge case: if ``block_values`` is empty, returns 0.0 (not NaN). This
    keeps downstream math from poisoning when a metric isn't vectorized.
    """
    if not block_values:
        return 0.0
    if rule not in VALID_RULES:
        raise ValueError(f"unknown aggregation rule {rule!r}; valid: {sorted(VALID_RULES)}")

    if rule == "leader":
        return float(max(block_values.values()))
    if rule == "max":
        return float(max(block_values.values()))
    if rule == "sum":
        return float(sum(block_values.values()))
    # weighted_mean
    weights = block_weights or DEFAULT_GDP_WEIGHTS_1998
    total_weight = sum(weights.get(b, 0.0) for b in block_values)
    if total_weight <= 0:
        # all weights zero → fall back to simple mean
        return float(sum(block_values.values()) / len(block_values))
    weighted_sum = sum(block_values[b] * weights.get(b, 0.0) for b in block_values)
    return float(weighted_sum / total_weight)
