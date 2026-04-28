# DRAFT - revisar com humano
"""Loader and validator for spec/geographic_blocks.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class GeographicBlock:
    id: str
    name: str
    scope: str
    population_share_1998: float
    gdp_share_1998: float
    tech_capacity_1998: float
    internet_penetration_1998: float
    rd_spending_share_1998: float
    notes: str = ""
    draft: bool = True


@dataclass
class SpilloverFriction:
    pair: str
    base: float
    modulators: List[Dict] = field(default_factory=list)
    draft: bool = True


@dataclass
class BlocksSpec:
    blocks: List[GeographicBlock]
    spillover_friction: Dict[str, SpilloverFriction]
    bass_p_innovation: float
    bass_q_imitation: float


def load_blocks(path: Path) -> BlocksSpec:
    """Loads spec/geographic_blocks.json into a typed BlocksSpec."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    blocks = [GeographicBlock(**b) for b in raw["blocks"]]
    sp_raw = raw.get("spillover_friction_matrix", {})
    spillover: Dict[str, SpilloverFriction] = {}
    for key, val in sp_raw.items():
        if key.startswith("_"):
            continue
        spillover[key] = SpilloverFriction(
            pair=key,
            base=val["base"],
            modulators=val.get("modulators", []),
            draft=val.get("draft", True),
        )
    bass = raw.get("bass_diffusion_defaults", {})
    return BlocksSpec(
        blocks=blocks,
        spillover_friction=spillover,
        bass_p_innovation=bass.get("p_innovation", 0.005),
        bass_q_imitation=bass.get("q_imitation", 0.4),
    )


def validate_blocks(spec: BlocksSpec) -> List[str]:
    errors: List[str] = []
    expected_ids = {"US", "EU", "CN", "RoW"}
    actual_ids = {b.id for b in spec.blocks}
    missing = expected_ids - actual_ids
    if missing:
        errors.append(f"missing block ids: {sorted(missing)}")
    extra = actual_ids - expected_ids
    if extra:
        errors.append(f"unexpected block ids: {sorted(extra)}")
    pop_sum = sum(b.population_share_1998 for b in spec.blocks)
    if not (0.99 <= pop_sum <= 1.01):
        errors.append(f"population shares sum to {pop_sum:.3f}, expected ~1.0")
    gdp_sum = sum(b.gdp_share_1998 for b in spec.blocks)
    if not (0.99 <= gdp_sum <= 1.01):
        errors.append(f"gdp shares sum to {gdp_sum:.3f}, expected ~1.0")
    for b in spec.blocks:
        for fname in ("tech_capacity_1998", "internet_penetration_1998"):
            v = getattr(b, fname)
            if not (0.0 <= v <= 1.0):
                errors.append(f"block {b.id}: {fname}={v} out of [0,1]")
    for key, sf in spec.spillover_friction.items():
        if not (0.0 <= sf.base <= 1.0):
            errors.append(f"spillover {key}: base {sf.base} out of [0,1]")
    return errors
