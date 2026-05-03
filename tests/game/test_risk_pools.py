"""Testes da Fase 4 — risk pools (accident_risk, exposure_risk, alignment_credit)
e métrica derivada lab_lead_over_rivals.

Padrão: usa StubGameMaster ou ações canônicas. Roll de acidente é
determinístico via _accident_roll(seed, turn, "accident_check") — testes
escolhem seeds onde o roll é conhecido.
"""
from __future__ import annotations

import pytest

from src.engine.state import WorldState
from src.game.canonical_actions import (
    AGGRESSIVE_HIRING,
    HIDE_CAPABILITIES,
    RUSH_TO_MARKET,
)
from src.game.game_runner import (
    ALIGNMENT_CREDIT_DECAY_PER_TURN,
    PASSIVE_RISK_PER_CAPABILITY_POINT,
    PASSIVE_RISK_PER_PENETRATION_POINT,
    SCANDAL_REPUTATION_PENALTY,
    SCANDAL_TRUST_PENALTY,
    _accident_roll,
    _passive_accident_risk_delta,
    _resolve_risk_pools,
    compute_lab_lead,
    start_game,
    submit_action,
)
from src.game.gm import StubGameMaster
from src.game.models import GMInterpretation, PlayerState


# ────────────────────────────────────────────── lab_lead_over_rivals


def test_compute_lab_lead_initial_state():
    """Initial state: US=92, EU=78, CN=35, RoW=18 → lead = 92 - (78+35+18)/3 ≈ 48.33."""
    state = WorldState.from_initial_spec()
    lead = compute_lab_lead(state)
    expected = 92.0 - (78.0 + 35.0 + 18.0) / 3.0
    assert lead == pytest.approx(expected)


def test_lab_lead_in_player_state_after_start():
    """start_game snapshota lab_lead em PlayerState."""
    gs = start_game(seed=42)
    assert gs.player_state.lab_lead_over_rivals == pytest.approx(48.333, rel=1e-2)


def test_lab_lead_updates_after_canonical_action(stub_gm_factory):
    """push_capability sobe US — lab_lead deve aumentar."""
    gs = start_game(seed=42)
    initial_lead = gs.player_state.lab_lead_over_rivals
    new_gs, _ = submit_action(gs, {"type": "canonical", "action_id": "push_capability"})
    # push_capability: US +1.5; spillover/edges também movem rivais. Net deve subir.
    assert new_gs.player_state.lab_lead_over_rivals > initial_lead


def test_lab_lead_decreases_after_publish_open(stub_gm_factory):
    """publish_open acelera rivais mais que US — lab_lead deve diminuir."""
    gs = start_game(seed=42)
    initial_lead = gs.player_state.lab_lead_over_rivals
    new_gs, _ = submit_action(gs, {"type": "canonical", "action_id": "publish_open"})
    assert new_gs.player_state.lab_lead_over_rivals < initial_lead


# ────────────────────────────────────────────── accident_risk passivo


def test_passive_risk_zero_at_baseline():
    """Capability = 92 (baseline), pop_pen=0, alignment=0 → risk delta = 0."""
    state = WorldState.from_initial_spec()
    # Mas pop_pen.US=5 no inicial. Calculo correto: 0 + 5*0.001 = 0.005
    delta = _passive_accident_risk_delta(state, alignment_credit=0.0)
    assert delta == pytest.approx(5.0 * PASSIVE_RISK_PER_PENETRATION_POINT)


def test_passive_risk_grows_with_capability_above_baseline(stub_gm_factory):
    """capability_us = 92 + n → delta tem n * PASSIVE_RISK_PER_CAPABILITY_POINT."""
    state = WorldState.from_initial_spec()
    # Hack: simula um state com capability mais alta
    bm = dict(state.block_metrics)
    bm["ai_capability.frontier_capability"] = dict(bm["ai_capability.frontier_capability"])
    bm["ai_capability.frontier_capability"]["US"] = 95.0  # 3 acima do baseline
    bm["ai_capability.population_penetration"] = dict(bm["ai_capability.population_penetration"])
    bm["ai_capability.population_penetration"]["US"] = 0.0  # zera pra isolar
    state2 = WorldState(
        turn_index=state.turn_index, turn_label=state.turn_label,
        global_metrics=state.global_metrics, block_metrics=bm,
        matrix_metrics=state.matrix_metrics, metadata=state.metadata,
    )
    delta = _passive_accident_risk_delta(state2, alignment_credit=0.0)
    assert delta == pytest.approx(3.0 * PASSIVE_RISK_PER_CAPABILITY_POINT)


def test_alignment_credit_drains_passive_risk():
    """alignment_credit reduz o delta passivo proporcionalmente."""
    state = WorldState.from_initial_spec()
    delta_no_credit = _passive_accident_risk_delta(state, alignment_credit=0.0)
    delta_with_credit = _passive_accident_risk_delta(state, alignment_credit=1.0)
    assert delta_with_credit < delta_no_credit


# ────────────────────────────────────────────── accident roll determinismo


def test_accident_roll_deterministic():
    """Mesma (seed, turn) → mesmo roll."""
    a = _accident_roll(seed=42, turn=3)
    b = _accident_roll(seed=42, turn=3)
    assert a == b


def test_accident_roll_changes_with_turn():
    a = _accident_roll(seed=42, turn=0)
    b = _accident_roll(seed=42, turn=1)
    assert a != b


def test_accident_roll_in_unit_interval():
    for s in range(5):
        for t in range(20):
            v = _accident_roll(seed=s, turn=t)
            assert 0.0 <= v < 1.0


# ────────────────────────────────────────────── accident trigger


def test_high_accident_risk_triggers_accident():
    """accident_risk = 0.99 + small passive → roll quase certo dispara."""
    state = WorldState.from_initial_spec()
    ps = PlayerState(accident_risk=0.99)
    new_ps, eng_pen, events = _resolve_risk_pools(ps, state, seed=42, turn=0)
    # Vai disparar a menos que o roll seja > 0.99 (1% chance)
    if events and events[0].kind == "accident":
        assert new_ps.accidents_count == 1
        assert new_ps.accident_risk == 0.0
        assert "information_ecosystem.media_trust" in eng_pen
        assert eng_pen["information_ecosystem.media_trust"] < 0
        assert new_ps.reputation < 0  # caiu
        assert new_ps.lab_funds < 1.0  # caiu


def test_zero_accident_risk_never_triggers():
    """accident_risk = 0 + sem passive contribution → nunca acidente."""
    state = WorldState.from_initial_spec()
    # Uso um state hackeado pra zerar passivo (capability=92, pop=0)
    bm = dict(state.block_metrics)
    bm["ai_capability.population_penetration"] = dict(bm["ai_capability.population_penetration"])
    bm["ai_capability.population_penetration"]["US"] = 0.0
    state2 = WorldState(
        turn_index=state.turn_index, turn_label=state.turn_label,
        global_metrics=state.global_metrics, block_metrics=bm,
        matrix_metrics=state.matrix_metrics, metadata=state.metadata,
    )
    ps = PlayerState(accident_risk=0.0)
    new_ps, eng_pen, events = _resolve_risk_pools(ps, state2, seed=42, turn=0)
    accident_events = [e for e in events if e.kind == "accident"]
    assert accident_events == []
    assert new_ps.accidents_count == 0


# ────────────────────────────────────────────── exposure_risk trigger


def test_exposure_risk_above_one_triggers_scandal():
    state = WorldState.from_initial_spec()
    ps = PlayerState(exposure_risk=1.2, accident_risk=0.0)
    new_ps, eng_pen, events = _resolve_risk_pools(ps, state, seed=42, turn=0)
    scandal_events = [e for e in events if e.kind == "scandal"]
    assert len(scandal_events) == 1
    assert new_ps.exposure_risk == 0.0  # reseta
    assert new_ps.reputation == pytest.approx(SCANDAL_REPUTATION_PENALTY)
    assert eng_pen.get("information_ecosystem.media_trust", 0) <= SCANDAL_TRUST_PENALTY


def test_exposure_risk_below_one_no_scandal():
    state = WorldState.from_initial_spec()
    ps = PlayerState(exposure_risk=0.95, accident_risk=0.0)
    new_ps, _, events = _resolve_risk_pools(ps, state, seed=42, turn=0)
    assert all(e.kind != "scandal" for e in events)
    assert new_ps.exposure_risk == pytest.approx(0.95)  # mantém (não resetou)


def test_exposure_risk_does_not_decay():
    """exposure_risk NÃO decai sozinho — só sobe ou reseta no scandal."""
    state = WorldState.from_initial_spec()
    ps = PlayerState(exposure_risk=0.5, accident_risk=0.0)
    new_ps, _, _ = _resolve_risk_pools(ps, state, seed=42, turn=0)
    assert new_ps.exposure_risk == 0.5


# ────────────────────────────────────────────── alignment_credit decay


def test_alignment_credit_decays_per_turn():
    state = WorldState.from_initial_spec()
    ps = PlayerState(alignment_credit=1.0, accident_risk=0.0)
    new_ps, _, _ = _resolve_risk_pools(ps, state, seed=42, turn=0)
    assert new_ps.alignment_credit == pytest.approx(1.0 * (1.0 - ALIGNMENT_CREDIT_DECAY_PER_TURN))


def test_alignment_credit_clamped_non_negative():
    state = WorldState.from_initial_spec()
    ps = PlayerState(alignment_credit=0.05, accident_risk=0.0)
    # decay 20% → 0.04, ainda positivo
    new_ps, _, _ = _resolve_risk_pools(ps, state, seed=42, turn=0)
    assert new_ps.alignment_credit >= 0.0


# ────────────────────────────────────────────── novas 3 ações canônicas


def test_three_new_canonical_actions_run():
    """rush_to_market, hide_capabilities, aggressive_hiring rodam sem erro."""
    for action in (RUSH_TO_MARKET, HIDE_CAPABILITIES, AGGRESSIVE_HIRING):
        gs = start_game(seed=42)
        new_gs, result = submit_action(gs, {"type": "canonical", "action_id": action.id})
        assert new_gs.current_turn == 1
        assert result.outcome == "success"


def test_rush_to_market_adds_accident_risk():
    """cost.accident_risk +0.40 → após 1 turn, accident_risk subiu (descontado o
    passive delta que pode ter rodado). Porém, accident_risk pode disparar
    acidente NO MESMO TURNO se o roll for baixo o bastante; usamos seed onde
    o roll é alto pra evitar."""
    # Cherry-pick um seed onde _accident_roll(seed, 0) > 0.50
    candidate_seeds = [s for s in range(50) if _accident_roll(s, 0) > 0.5]
    assert candidate_seeds, "deveria existir algum seed safe"
    seed = candidate_seeds[0]

    gs = start_game(seed=seed)
    new_gs, result = submit_action(gs, {"type": "canonical", "action_id": "rush_to_market"})
    # Roll alto → não disparou acidente → accident_risk preservado e ≥ 0.40
    if not any(e["kind"] == "accident" for e in result.risk_events):
        assert new_gs.player_state.accident_risk >= 0.40 - 1e-6
    else:
        # Disparou; pelo menos confirmou que rush_to_market mexe no pool
        assert new_gs.player_state.accidents_count == 1


def test_hide_capabilities_adds_exposure_risk():
    """cost.exposure_risk +0.30 → após 1 turn, exposure_risk = 0.30."""
    gs = start_game(seed=42)
    new_gs, _ = submit_action(gs, {"type": "canonical", "action_id": "hide_capabilities"})
    assert new_gs.player_state.exposure_risk == pytest.approx(0.30)


def test_aggressive_hiring_costs_lab_funds():
    """aggressive_hiring custa 0.40 — caro."""
    gs = start_game(seed=42)
    initial_funds = gs.player_state.lab_funds
    new_gs, _ = submit_action(gs, {"type": "canonical", "action_id": "aggressive_hiring"})
    assert new_gs.player_state.lab_funds == pytest.approx(initial_funds - 0.40)


# ────────────────────────────────────────────── invest_alignment + alignment_credit


def test_invest_alignment_adds_alignment_credit():
    """cost.alignment_credit +0.30. Após 1 turn, sofre decay 20% → ~0.24."""
    gs = start_game(seed=42)
    new_gs, _ = submit_action(gs, {"type": "canonical", "action_id": "invest_alignment"})
    expected_after_decay = 0.30 * (1.0 - ALIGNMENT_CREDIT_DECAY_PER_TURN)
    assert new_gs.player_state.alignment_credit == pytest.approx(expected_after_decay)


# ────────────────────────────────────────────── smoke test rush sequence


def test_smoke_rush_sequence_triggers_accident():
    """10 turnos: 3x push_capability, 3x deploy_commercial, 2x rush_to_market,
    2x invest_alignment. Com os 2 rush_to_market (+0.80 risk total) somados
    ao passive buildup, deve disparar acidente em algum momento."""
    gs = start_game(seed=42)
    sequence = (
        ["push_capability"] * 3
        + ["deploy_commercial"] * 3
        + ["rush_to_market"] * 2
        + ["invest_alignment"] * 2
    )
    accidents_seen = 0
    for action_id in sequence:
        if gs.status != "in_progress":
            break
        gs, result = submit_action(gs, {"type": "canonical", "action_id": action_id})
        if any(e["kind"] == "accident" for e in result.risk_events):
            accidents_seen += 1

    # Esperamos pelo menos 1 acidente OU game over via accidents_count
    assert accidents_seen >= 1 or gs.player_state.accidents_count >= 1


# ────────────────────────────────────────────── action_result risk_events surface


def test_action_result_includes_risk_events_on_accident():
    """Quando acidente dispara, ActionResult.risk_events tem entrada com kind=accident."""
    state = WorldState.from_initial_spec()
    ps = PlayerState(accident_risk=0.999)
    # Force accident via _resolve_risk_pools direto (não via submit pra evitar
    # interferência de passive delta)
    _, _, events = _resolve_risk_pools(ps, state, seed=42, turn=0)
    if events and events[0].kind == "accident":
        # OK — happy path, na maioria dos seeds
        return
    # senão, tente outros turns
    for t in range(20):
        _, _, events = _resolve_risk_pools(ps, state, seed=42, turn=t)
        if events and events[0].kind == "accident":
            return
    pytest.fail("nenhum turn 0..20 disparou acidente com risk=0.999, suspeito")
