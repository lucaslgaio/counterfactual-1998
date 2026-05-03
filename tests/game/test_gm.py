"""Testes do GM-LLM — guardrails (clip, roll determinístico) sem chamada de rede."""
from __future__ import annotations

import pytest

from src.game.config import CATEGORY_CAPS
from src.game.gm import (
    StubGameMaster,
    _hash_action,
    clip_interpretation,
    roll_outcome,
)
from src.game.models import GMInterpretation


# --------------------------- roll_outcome


def test_roll_outcome_deterministic_same_inputs():
    a = roll_outcome(0.5, seed=42, turn=0, action_hash="abc")
    b = roll_outcome(0.5, seed=42, turn=0, action_hash="abc")
    assert a == b


def test_roll_outcome_changes_with_turn():
    a = roll_outcome(0.5, seed=42, turn=0, action_hash="abc")
    b = roll_outcome(0.5, seed=42, turn=1, action_hash="abc")
    assert a != b


def test_roll_outcome_success_p_one_always_succeeds():
    for seed in range(5):
        for turn in range(10):
            roll, outcome = roll_outcome(1.0, seed=seed, turn=turn, action_hash=str(turn))
            assert outcome == "success", f"roll={roll}, success_p=1 should always succeed"


def test_roll_outcome_success_p_zero_never_full_success():
    for seed in range(5):
        for turn in range(10):
            roll, outcome = roll_outcome(0.0, seed=seed, turn=turn, action_hash=str(turn))
            assert outcome != "success"


def test_roll_outcome_outcomes_in_set():
    valid = {"success", "partial_failure", "total_failure"}
    for sp in [0.0, 0.25, 0.5, 0.75, 1.0]:
        for t in range(10):
            _, outcome = roll_outcome(sp, seed=42, turn=t, action_hash="x")
            assert outcome in valid


# --------------------------- clip_interpretation


def test_clip_does_not_alter_within_caps():
    cap = CATEGORY_CAPS["research"]["max_metric_delta"]
    interp = GMInterpretation(
        classification="research",
        plausible=True,
        affected_metrics={"ai_capability.frontier_capability.US": cap - 0.1},
        side_effects={},
        success_p=0.7,
        narrative_seed="x",
    )
    clipped, fields = clip_interpretation(interp)
    assert fields == []
    assert clipped.affected_metrics["ai_capability.frontier_capability.US"] == pytest.approx(cap - 0.1)


def test_clip_caps_oversize_positive_delta():
    cap = CATEGORY_CAPS["research"]["max_metric_delta"]
    big = cap * 5
    interp = GMInterpretation(
        classification="research",
        plausible=True,
        affected_metrics={"ai_capability.frontier_capability.US": big},
        side_effects={},
        success_p=0.7,
        narrative_seed="x",
    )
    clipped, fields = clip_interpretation(interp)
    assert clipped.affected_metrics["ai_capability.frontier_capability.US"] == pytest.approx(cap)
    assert any("affected_metrics.ai_capability.frontier_capability.US" in f for f in fields)


def test_clip_caps_negative_delta_symmetrically():
    cap = CATEGORY_CAPS["lobby"]["max_metric_delta"]
    big_neg = -cap * 3
    interp = GMInterpretation(
        classification="lobby",
        plausible=True,
        affected_metrics={"governance.democracy_index.US": big_neg},
        side_effects={},
        success_p=0.7,
        narrative_seed="x",
    )
    clipped, fields = clip_interpretation(interp)
    assert clipped.affected_metrics["governance.democracy_index.US"] == pytest.approx(-cap)
    assert any("affected_metrics" in f for f in fields)


def test_clip_drops_metrics_beyond_max_n():
    max_n = CATEGORY_CAPS["lobby"]["max_metrics_affected"]
    affected = {f"governance.democracy_index.{b}": 0.1 + i*0.1
                for i, b in enumerate(("US", "EU", "CN", "RoW"))}
    interp = GMInterpretation(
        classification="lobby",
        plausible=True,
        affected_metrics=affected,
        side_effects={},
        success_p=0.5,
        narrative_seed="x",
    )
    clipped, fields = clip_interpretation(interp)
    assert len(clipped.affected_metrics) <= max_n
    if len(affected) > max_n:
        assert any("dropped.affected_metrics" in f for f in fields)


def test_clip_zeroes_rejected_or_implausible():
    interp = GMInterpretation(
        classification="research",
        plausible=False,
        affected_metrics={"ai_capability.frontier_capability.US": 5.0},
        side_effects={"information_ecosystem.media_trust": -2.0},
        cost={"lab_funds": -0.5},
        success_p=0.9,
        narrative_seed="x",
        rejection_reason="implausível",
    )
    clipped, _ = clip_interpretation(interp)
    assert clipped.classification == "rejected"
    assert clipped.affected_metrics == {}
    assert clipped.side_effects == {}
    assert clipped.cost == {}


# --------------------------- StubGameMaster


def test_stub_gm_returns_default_interpretation():
    gm = StubGameMaster()
    interp = gm.interpret(
        "test prompt",
        year=1998.0, turn=0,
        mission_name="x", mission_description="y",
        engine_state_summary="", player_state={},
        recent_history=[],
    )
    assert interp.classification == "research"
    assert interp.plausible is True


def test_stub_gm_with_fixed_interpretation():
    fixed = GMInterpretation(
        classification="lobby", plausible=True, success_p=0.3,
        affected_metrics={"governance.democracy_index.US": 0.2},
        narrative_seed="seed",
    )
    gm = StubGameMaster(fixed_interpretation=fixed)
    out = gm.interpret(
        "x", year=1998.0, turn=0, mission_name="m", mission_description="d",
        engine_state_summary="", player_state={}, recent_history=[],
    )
    assert out is fixed


def test_hash_action_stable_across_calls():
    h1 = _hash_action("recrutamos 10 PhDs em alignment")
    h2 = _hash_action("recrutamos 10 PhDs em alignment")
    assert h1 == h2
    assert _hash_action("outro texto") != h1
