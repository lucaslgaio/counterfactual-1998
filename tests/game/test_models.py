"""Testes dos modelos Pydantic do Modo Jogo."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.game.models import (
    ActionResult,
    Condition,
    GameState,
    GMInterpretation,
    Mission,
    PlayerState,
    TurnRecord,
)


def test_condition_validates_operator_enum():
    Condition(metric="x", scope="player", operator=">=", threshold=0.0)
    with pytest.raises(ValidationError):
        Condition(metric="x", scope="player", operator="===", threshold=0.0)


def test_condition_validates_scope_enum():
    Condition(metric="x", scope="engine", operator="==", threshold=0)
    with pytest.raises(ValidationError):
        Condition(metric="x", scope="cosmos", operator="==", threshold=0)


def test_gm_interpretation_clamps_success_p_in_range():
    GMInterpretation(
        classification="research", plausible=True, success_p=0.5,
    )
    with pytest.raises(ValidationError):
        GMInterpretation(
            classification="research", plausible=True, success_p=1.5,
        )
    with pytest.raises(ValidationError):
        GMInterpretation(
            classification="research", plausible=True, success_p=-0.1,
        )


def test_player_state_defaults():
    ps = PlayerState()
    assert ps.lab_funds == 1.0
    assert ps.accidents_count == 0
    assert 0.0 <= ps.reputation <= 1.0


def test_action_result_defaults():
    ar = ActionResult(
        action_type="canonical",
        raw_input="push_capability",
        roll=0.42,
        outcome="success",
    )
    assert ar.applied_deltas == {}
    assert ar.clipped is False
    assert ar.clipped_fields == []


def test_game_state_round_trips_via_model_dump():
    """GameState deve serializar e re-hidratar."""
    from src.game.missions import MISSION_AGI_ALIGNED
    gs = GameState(
        game_id="abc123",
        seed=42,
        mission=MISSION_AGI_ALIGNED,
        current_turn=0,
        engine_state={"turn_index": 0, "turn_label": "1998-S1",
                      "global_metrics": {}, "block_metrics": {}, "matrix_metrics": {},
                      "metadata": {}},
        player_state=PlayerState(),
    )
    dumped = gs.model_dump()
    re = GameState(**dumped)
    assert re.game_id == "abc123"
    assert re.mission.id == MISSION_AGI_ALIGNED.id
    assert re.status == "in_progress"
