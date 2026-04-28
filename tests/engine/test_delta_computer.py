"""Tests for src/engine/delta_computer.py."""
from __future__ import annotations

import pytest

from src.engine.delta_computer import (
    CausalLinkActive,
    DeltaPackage,
    compute_turn_deltas,
)
from src.engine.simulation import build_spec_bundle
from src.engine.state import WorldState


def test_delta_package_combines_layers():
    pkg = DeltaPackage()
    pkg.add_to_global("financial_markets.global_index", 5.0, source="edge")
    pkg.add_to_global("financial_markets.global_index", -3.0, source="exogenous")
    assert pkg.global_deltas["financial_markets.global_index"] == 2.0
    assert pkg.edge_global_deltas["financial_markets.global_index"] == 5.0
    assert pkg.exogenous_global_deltas["financial_markets.global_index"] == -3.0


def test_compute_turn_deltas_initial_state_no_event_no_shock():
    """Without event/shock, deltas come only from edges + spillover. Result
    should be a non-empty package with finite values."""
    spec = build_spec_bundle()
    state = WorldState.from_initial_spec()
    pkg = compute_turn_deltas(state, None, None, None, spec)
    # Must produce SOME delta given 130 active edges
    assert pkg.global_deltas or pkg.block_deltas
    # All deltas should be finite
    for v in pkg.global_deltas.values():
        assert v == v and v != float("inf") and v != float("-inf")


def test_compute_turn_deltas_records_causal_links():
    spec = build_spec_bundle()
    state = WorldState.from_initial_spec()
    pkg = compute_turn_deltas(state, None, None, None, spec)
    # Top contributors are kept (up to 8)
    assert 0 <= len(pkg.causal_links_active) <= 8
    for link in pkg.causal_links_active:
        assert link.edge_id.startswith("e_")
        assert isinstance(link.contribution, float)


def test_compute_turn_deltas_user_input_routed():
    """User input deltas should land in the exogenous bucket exactly as given —
    edges may add their own contributions to the same metric, but the
    exogenous bucket is preserved untouched for traceability."""
    spec = build_spec_bundle()
    state = WorldState.from_initial_spec()
    user_in = {"financial_markets.global_index": 10.0}
    pkg = compute_turn_deltas(state, None, None, user_in, spec)
    # User input is exogenous — landed in exogenous_global_deltas
    assert pkg.exogenous_global_deltas.get("financial_markets.global_index", 0.0) == 10.0
    # Combined view = exogenous + edge contributions; the exogenous part is
    # always exactly the user_input value.
    edge_part = pkg.edge_global_deltas.get("financial_markets.global_index", 0.0)
    combined = pkg.global_deltas.get("financial_markets.global_index", 0.0)
    assert abs(combined - (10.0 + edge_part)) < 1e-9


def test_causal_link_to_json_round_trip():
    link = CausalLinkActive(
        edge_id="e_001",
        source="ai_capability.frontier_capability",
        target="labor_market.automation_exposure",
        source_value=92.0,
        contribution=3.68,
        form="linear",
    )
    js = link.to_json()
    assert js["edge_id"] == "e_001"
    assert js["form"] == "linear"
