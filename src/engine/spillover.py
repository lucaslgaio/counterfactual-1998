"""Bass-style cross-block diffusion for vectorized metrics.

The spec defines a directional friction matrix between blocks
(``geographic_blocks.json :: spillover_friction_matrix``). Higher friction means
slower transfer. This module turns each pair (source → target) into a delta
proportional to the gap, scaled by friction and a single diffusion alpha.

Convention (matches spec): friction values are 0..1 where 1.0 means
*frictionless* and 0 means *fully isolated*. We multiply the gap-driven
delta by ``friction`` directly (no inversion), so high friction → fast
transfer, low friction → slow transfer.

Per-turn delta for each (source, target) ordered pair:

    delta_target += diffusion_alpha * friction[source→target] * (source_value - target_value)

Total delta for each block is the sum over all source blocks (excluding self).
"""
from __future__ import annotations

from typing import Dict, Optional

from src.spec.blocks import BlocksSpec

BLOCKS = ("US", "EU", "CN", "RoW")


def compute_spillover(
    block_values: Dict[str, float],
    friction_lookup: Dict[str, float],
    diffusion_alpha: float = 0.05,
) -> Dict[str, float]:
    """Compute the spillover delta for each block.

    Args:
        block_values: {block: current_value}.
        friction_lookup: {f"{src}_to_{tgt}": friction_0_to_1}.
        diffusion_alpha: per-turn rate constant.

    Returns:
        {block: delta_from_spillover}. Sum across blocks ≈ 0 when diffusion_alpha
        is small and friction is symmetric (conservation property).
    """
    deltas: Dict[str, float] = {b: 0.0 for b in block_values}
    for tgt in block_values:
        for src in block_values:
            if src == tgt:
                continue
            key = f"{src}_to_{tgt}"
            f = friction_lookup.get(key, 0.0)
            gap = block_values[src] - block_values[tgt]
            deltas[tgt] += diffusion_alpha * f * gap
    return deltas


def build_friction_lookup(blocks_spec: BlocksSpec) -> Dict[str, float]:
    """Flatten spillover_friction (a dict of SpilloverFriction objects) into
    a simple {pair: base} map. Modulators are ignored at MVP — calibration
    in Etapa 5 may activate them.
    """
    out: Dict[str, float] = {}
    for pair, sf in blocks_spec.spillover_friction.items():
        out[pair] = float(sf.base)
    return out
