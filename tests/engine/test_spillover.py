"""Tests for src/engine/spillover.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.engine.spillover import (
    BLOCKS,
    build_friction_lookup,
    compute_spillover,
)
from src.spec.blocks import load_blocks

SPEC_DIR = Path(__file__).parent.parent.parent / "spec"


def test_build_friction_lookup_from_real_spec():
    blocks_spec = load_blocks(SPEC_DIR / "geographic_blocks.json")
    lookup = build_friction_lookup(blocks_spec)
    # All ordered pairs (excluding self) should be present.
    for src in BLOCKS:
        for tgt in BLOCKS:
            if src == tgt:
                continue
            key = f"{src}_to_{tgt}"
            assert key in lookup, f"missing {key} in friction lookup"
            assert 0.0 <= lookup[key] <= 1.0


def test_no_gap_produces_no_spillover():
    """All blocks at same value → delta=0 everywhere."""
    bv = {b: 50.0 for b in BLOCKS}
    friction = {f"{s}_to_{t}": 0.5 for s in BLOCKS for t in BLOCKS if s != t}
    deltas = compute_spillover(bv, friction)
    for b, d in deltas.items():
        assert abs(d) < 1e-12, f"expected ~0, got {d} for {b}"


def test_higher_friction_means_faster_convergence():
    """Run 100 sim steps; high friction should converge faster than low."""

    def simulate(friction_value: float, n_steps: int = 100) -> Dict[str, float]:
        bv = {"US": 100.0, "EU": 0.0, "CN": 0.0, "RoW": 0.0}
        friction = {
            f"{s}_to_{t}": friction_value
            for s in BLOCKS
            for t in BLOCKS
            if s != t
        }
        for _ in range(n_steps):
            d = compute_spillover(bv, friction, diffusion_alpha=0.05)
            bv = {k: bv[k] + d[k] for k in bv}
        return bv

    high_friction_state = simulate(0.9)
    low_friction_state = simulate(0.1)

    # With high friction (= less resistance), US drops faster toward mean
    assert high_friction_state["US"] < low_friction_state["US"]


def test_conservation_approximately_holds():
    """Spillover shouldn't create or destroy value when alpha is small."""
    bv = {"US": 100, "EU": 60, "CN": 40, "RoW": 20}
    friction = {f"{s}_to_{t}": 0.5 for s in BLOCKS for t in BLOCKS if s != t}
    deltas = compute_spillover(bv, friction, diffusion_alpha=0.01)
    total = sum(deltas.values())
    assert abs(total) < 1e-6, f"non-conservative spillover: total delta = {total}"


def test_isolated_block_no_spillover_in_or_out():
    """If all friction TO/FROM a block is zero, that block's delta is zero
    AND it doesn't perturb other blocks (only their inflow from this block)."""
    bv = {"US": 100, "EU": 50, "CN": 0, "RoW": 50}
    # No friction touching CN at all
    friction = {f"{s}_to_{t}": 0.0 for s in BLOCKS for t in BLOCKS if s != t}
    # Reactivate non-CN edges
    friction["US_to_EU"] = 0.5
    friction["EU_to_US"] = 0.5
    deltas = compute_spillover(bv, friction)
    assert abs(deltas["CN"]) < 1e-9
    assert deltas["US"] != 0  # affected by EU
    assert deltas["EU"] != 0  # affected by US


# Used by helper above
from typing import Dict
