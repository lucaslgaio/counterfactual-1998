"""Tests for src/spec/blocks.py."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.spec.blocks import (
    BlocksSpec,
    GeographicBlock,
    SpilloverFriction,
    load_blocks,
    validate_blocks,
)

SPEC_DIR = Path(__file__).parent.parent.parent / "spec"


def test_load_real_blocks():
    spec = load_blocks(SPEC_DIR / "geographic_blocks.json")
    assert len(spec.blocks) == 4
    block_ids = {b.id for b in spec.blocks}
    assert block_ids == {"US", "EU", "CN", "RoW"}


def test_real_blocks_pass_validation():
    spec = load_blocks(SPEC_DIR / "geographic_blocks.json")
    errors = validate_blocks(spec)
    assert not errors, f"validation failed: {errors}"


def test_real_blocks_have_spillover_matrix():
    spec = load_blocks(SPEC_DIR / "geographic_blocks.json")
    assert len(spec.spillover_friction) >= 12, "expected at least 12 directional pairs"


def test_validation_catches_missing_block():
    spec = BlocksSpec(
        blocks=[
            GeographicBlock(id="US", name="x", scope="x",
                            population_share_1998=0.5, gdp_share_1998=0.5,
                            tech_capacity_1998=1.0, internet_penetration_1998=0.5,
                            rd_spending_share_1998=0.5),
            GeographicBlock(id="EU", name="x", scope="x",
                            population_share_1998=0.5, gdp_share_1998=0.5,
                            tech_capacity_1998=0.7, internet_penetration_1998=0.5,
                            rd_spending_share_1998=0.5),
        ],
        spillover_friction={},
        bass_p_innovation=0.005,
        bass_q_imitation=0.4,
    )
    errors = validate_blocks(spec)
    assert any("missing block ids" in e for e in errors)


def test_validation_catches_bad_population_sum():
    spec = BlocksSpec(
        blocks=[
            GeographicBlock(id=bid, name="x", scope="x",
                            population_share_1998=0.4, gdp_share_1998=0.25,
                            tech_capacity_1998=0.5, internet_penetration_1998=0.5,
                            rd_spending_share_1998=0.25)
            for bid in ("US", "EU", "CN", "RoW")
        ],
        spillover_friction={},
        bass_p_innovation=0.005,
        bass_q_imitation=0.4,
    )
    errors = validate_blocks(spec)
    assert any("population shares sum" in e for e in errors)


def test_validation_catches_out_of_range():
    spec = BlocksSpec(
        blocks=[
            GeographicBlock(id="US", name="x", scope="x",
                            population_share_1998=0.25, gdp_share_1998=0.25,
                            tech_capacity_1998=2.0, internet_penetration_1998=0.5,
                            rd_spending_share_1998=0.25),
            GeographicBlock(id="EU", name="x", scope="x",
                            population_share_1998=0.25, gdp_share_1998=0.25,
                            tech_capacity_1998=0.7, internet_penetration_1998=0.5,
                            rd_spending_share_1998=0.25),
            GeographicBlock(id="CN", name="x", scope="x",
                            population_share_1998=0.25, gdp_share_1998=0.25,
                            tech_capacity_1998=0.3, internet_penetration_1998=0.5,
                            rd_spending_share_1998=0.25),
            GeographicBlock(id="RoW", name="x", scope="x",
                            population_share_1998=0.25, gdp_share_1998=0.25,
                            tech_capacity_1998=0.4, internet_penetration_1998=0.5,
                            rd_spending_share_1998=0.25),
        ],
        spillover_friction={},
        bass_p_innovation=0.005,
        bass_q_imitation=0.4,
    )
    errors = validate_blocks(spec)
    assert any("tech_capacity_1998=2.0 out of [0,1]" in e for e in errors)
