"""Testes do game_runner — fluxo completo com GM mockado."""
from __future__ import annotations

import pytest

from src.game.canonical_actions import CANONICAL_ACTIONS
from src.game.game_runner import (
    _evaluate_condition,
    _evaluate_status,
    _year_from_turn_label,
    start_game,
    submit_action,
)
from src.game.gm import StubGameMaster
from src.game.missions import MISSION_AGI_ALIGNED
from src.game.models import (
    Condition,
    GMInterpretation,
    PlayerState,
)
from src.engine.state import WorldState


# --------------------------- start_game


def test_start_game_returns_initial_state():
    gs = start_game(seed=42)
    assert gs.current_turn == 0
    assert gs.status == "in_progress"
    assert gs.player_state.lab_funds == 1.0
    assert gs.player_state.accidents_count == 0
    assert gs.engine_state["turn_index"] == 0
    assert gs.engine_state["turn_label"] == "1998-S1"


def test_start_game_uses_default_mission():
    gs = start_game(seed=1)
    assert gs.mission.id == MISSION_AGI_ALIGNED.id


def test_start_game_assigns_unique_game_id():
    a = start_game(seed=1)
    b = start_game(seed=1)
    assert a.game_id != b.game_id


# --------------------------- canonical action


def test_submit_canonical_action_advances_turn():
    gs = start_game(seed=42)
    new_gs, result = submit_action(gs, {"type": "canonical", "action_id": "push_capability"})
    assert new_gs.current_turn == 1
    # engine_state agora é 1998-S2 (próximo semestre); o registro foi pra 1998-S1
    assert new_gs.engine_state["turn_label"] == "1998-S2"
    assert result.action_type == "canonical"
    assert result.outcome == "success"  # canonical sempre success_p=1


def test_canonical_action_applies_costs_to_player_state():
    gs = start_game(seed=42)
    initial_funds = gs.player_state.lab_funds
    new_gs, _ = submit_action(gs, {"type": "canonical", "action_id": "push_capability"})
    assert new_gs.player_state.lab_funds < initial_funds  # consumiu lab_funds


def test_canonical_action_writes_history_entry():
    gs = start_game(seed=42)
    new_gs, _ = submit_action(gs, {"type": "canonical", "action_id": "push_capability"})
    assert len(new_gs.history) == 1
    record = new_gs.history[0]
    assert record.turn == 0
    # registro = semestre que foi jogado (1998-S1), não o próximo
    assert record.turn_label == "1998-S1"
    assert record.action_result.action_type == "canonical"


def test_canonical_action_unknown_id_raises():
    gs = start_game(seed=42)
    with pytest.raises(KeyError):
        submit_action(gs, {"type": "canonical", "action_id": "nonexistent"})


def test_each_canonical_action_runs_without_error():
    """Smoke: cada uma das 5 ações canônicas deve completar 1 turno."""
    for action in CANONICAL_ACTIONS:
        gs = start_game(seed=42)
        new_gs, result = submit_action(gs, {"type": "canonical", "action_id": action.id})
        assert new_gs.current_turn == 1
        assert result.outcome == "success"


# --------------------------- free action with mocked GM


def test_submit_free_action_uses_provided_gm(stub_gm_factory):
    gs = start_game(seed=42)
    gm = stub_gm_factory(success_p=1.0)
    new_gs, result = submit_action(
        gs,
        {"type": "free", "prompt": "Investimos forte em segurança."},
        gm=gm,
    )
    assert result.action_type == "free"
    assert result.interpretation is not None
    assert result.outcome == "success"
    assert new_gs.current_turn == 1


def test_free_action_empty_prompt_raises():
    gs = start_game(seed=42)
    with pytest.raises(ValueError):
        submit_action(gs, {"type": "free", "prompt": "   "}, gm=StubGameMaster())


def test_free_action_partial_failure_scales_down(stub_gm_factory):
    gs = start_game(seed=42)
    # success_p=0 garante que NÃO será success integral. Vai cair em
    # partial_failure ou total_failure dependendo do roll.
    gm = stub_gm_factory(success_p=0.0,
                         affected_metrics={"ai_capability.frontier_capability.US": 1.0},
                         side_effects={"information_ecosystem.media_trust": -0.5})
    new_gs, result = submit_action(
        gs, {"type": "free", "prompt": "x"}, gm=gm,
    )
    assert result.outcome in ("partial_failure", "total_failure")
    if result.outcome == "partial_failure":
        # affected escalado por 0.3, side_effect integral
        assert result.applied_deltas.get("ai_capability.frontier_capability.US", 0) == pytest.approx(0.3)
        assert result.applied_deltas.get("information_ecosystem.media_trust", 0) == pytest.approx(-0.5)
    else:  # total_failure: affected zerados, side_effect integral, custo extra
        assert "ai_capability.frontier_capability.US" not in result.applied_deltas
        assert result.applied_deltas.get("information_ecosystem.media_trust", 0) == pytest.approx(-0.5)


def test_free_action_rejected_applies_zero_deltas(stub_gm_factory):
    gs = start_game(seed=42)
    gm = stub_gm_factory(plausible=False, classification="research",
                         rejection_reason="ação implausível para 1998")
    new_gs, result = submit_action(gs, {"type": "free", "prompt": "x"}, gm=gm)
    assert result.applied_deltas == {}
    # ainda avança o turno (semestre passa mesmo se ação foi rejeitada)
    assert new_gs.current_turn == 1


# --------------------------- determinism


def test_two_identical_runs_produce_same_result(stub_gm_factory):
    """Determinismo: mesmo seed + mesma ação → mesmo state."""
    gm1 = stub_gm_factory(success_p=0.5)
    gm2 = stub_gm_factory(success_p=0.5)
    gs1 = start_game(seed=42, game_id="fixed1")
    gs2 = start_game(seed=42, game_id="fixed2")
    a1, r1 = submit_action(gs1, {"type": "free", "prompt": "ação X"}, gm=gm1)
    a2, r2 = submit_action(gs2, {"type": "free", "prompt": "ação X"}, gm=gm2)
    assert r1.roll == r2.roll
    assert r1.outcome == r2.outcome
    assert a1.engine_state == a2.engine_state


# --------------------------- accident logic


def test_triggers_accident_increments_count_on_failure(stub_gm_factory):
    gs = start_game(seed=42)
    gm = stub_gm_factory(triggers_accident=True, success_p=0.0)
    new_gs, result = submit_action(gs, {"type": "free", "prompt": "deploy rushed"}, gm=gm)
    assert result.outcome != "success"
    assert new_gs.player_state.accidents_count >= 1


def test_triggers_accident_does_not_count_on_success(stub_gm_factory):
    gs = start_game(seed=42)
    gm = stub_gm_factory(triggers_accident=True, success_p=1.0)
    new_gs, result = submit_action(gs, {"type": "free", "prompt": "narrow miss"}, gm=gm)
    assert result.outcome == "success"
    assert new_gs.player_state.accidents_count == 0


# --------------------------- win/lose evaluation


def test_evaluate_condition_player_field():
    ps = PlayerState(lab_funds=0.0)
    cond = Condition(metric="lab_funds", scope="player", operator="<=", threshold=0.0)
    state = WorldState.from_initial_spec()
    assert _evaluate_condition(cond, state, ps, current_turn=5)


def test_evaluate_condition_engine_field_with_block_suffix():
    state = WorldState.from_initial_spec()
    cond = Condition(
        metric="ai_capability.frontier_capability.US",
        scope="engine", operator=">=", threshold=90.0,
    )
    assert _evaluate_condition(cond, state, PlayerState(), current_turn=5)


def test_evaluate_condition_at_turn_window():
    state = WorldState.from_initial_spec()
    cond = Condition(
        metric="ai_capability.frontier_capability.US",
        scope="engine", operator=">=", threshold=0,
        at_turn=10,
    )
    assert not _evaluate_condition(cond, state, PlayerState(), current_turn=5)
    assert _evaluate_condition(cond, state, PlayerState(), current_turn=10)


def test_evaluate_status_lose_takes_precedence():
    """Acidente disparado → game lost imediatamente."""
    state = WorldState.from_initial_spec()
    ps = PlayerState(accidents_count=1)
    status, msg = _evaluate_status(MISSION_AGI_ALIGNED, state, ps, current_turn=2)
    assert status == "lost"
    assert msg is not None


def test_evaluate_status_in_progress_at_start():
    state = WorldState.from_initial_spec()
    ps = PlayerState()
    status, msg = _evaluate_status(MISSION_AGI_ALIGNED, state, ps, current_turn=1)
    assert status == "in_progress"
    assert msg is None


def test_lose_triggered_when_lab_funds_zero():
    state = WorldState.from_initial_spec()
    ps = PlayerState(lab_funds=0.0)
    status, _ = _evaluate_status(MISSION_AGI_ALIGNED, state, ps, current_turn=3)
    assert status == "lost"


# --------------------------- helpers


def test_year_from_turn_label():
    assert _year_from_turn_label("1998-S1") == 1998.0
    assert _year_from_turn_label("1998-S2") == 1998.5
    assert _year_from_turn_label("2026-S2") == 2026.5


# --------------------------- end-to-end smoke


def test_smoke_full_5_turn_game(stub_gm_factory):
    """Smoke: 3 ações canônicas + 2 livres (GM mockado), termina sem erro."""
    gs = start_game(seed=42)

    # Turn 0: push_capability (canonical)
    gs, _ = submit_action(gs, {"type": "canonical", "action_id": "push_capability"})
    assert gs.current_turn == 1

    # Turn 1: invest_alignment (canonical)
    gs, _ = submit_action(gs, {"type": "canonical", "action_id": "invest_alignment"})
    assert gs.current_turn == 2

    # Turn 2: government_partnership (canonical)
    gs, _ = submit_action(gs, {"type": "canonical", "action_id": "government_partnership"})
    assert gs.current_turn == 3

    # Turn 3: ação livre (research moderada)
    gm = stub_gm_factory(
        classification="research", success_p=0.9,
        affected_metrics={"ai_capability.frontier_capability.US": 0.5},
        cost={"lab_funds": -0.05},
    )
    gs, _ = submit_action(gs, {"type": "free", "prompt": "Recrutamos PhDs em alignment"}, gm=gm)
    assert gs.current_turn == 4

    # Turn 4: ação livre (lobby)
    gm2 = stub_gm_factory(
        classification="lobby", success_p=0.4,
        affected_metrics={"governance.ai_regulation_maturity.US": 0.3},
        cost={"lab_funds": -0.03},
    )
    gs, _ = submit_action(gs, {"type": "free", "prompt": "Lobby em DC"}, gm=gm2)
    assert gs.current_turn == 5

    # Geral: 5 turnos, sem game over
    assert len(gs.history) == 5
    assert gs.status in ("in_progress", "won", "lost")  # estável e enumerado
    # Últimos 2 records foram free
    assert gs.history[-1].action_result.action_type == "free"
    assert gs.history[-2].action_result.action_type == "free"


def test_cannot_submit_after_game_over(stub_gm_factory):
    gs = start_game(seed=42)
    # Força acidente p/ derrota imediata
    gm = stub_gm_factory(triggers_accident=True, success_p=0.0)
    gs, _ = submit_action(gs, {"type": "free", "prompt": "x"}, gm=gm)
    assert gs.status == "lost"
    with pytest.raises(ValueError):
        submit_action(gs, {"type": "canonical", "action_id": "push_capability"})
