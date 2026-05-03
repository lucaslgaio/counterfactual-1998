"""Game runner — orquestra um turno de jogo.

Fluxo de submit_action:
1. Resolve a ação:
   - canonical: pega CanonicalAction.deltas/cost; cria GMInterpretation sintética
     (success_p=1.0, classification fixa "research" como placeholder).
   - free: chama gm.interpret(prompt, ...) → GMInterpretation; clipa contra caps.
2. Faz roll determinístico (success_p, seed, turn, action_hash).
3. Calcula `applied_engine_deltas` (motor) e `applied_player_deltas` conforme
   outcome (success / partial / total / rejected).
4. Aplica `applied_player_deltas` no PlayerState (custo da ação).
5. Atualiza risk pools:
   - passive accident_risk: cresce com capability acima de 92 + penetração;
     drena via alignment_credit
   - decay alignment_credit (20%/turno)
   - roll determinístico de acidente (seed, turn, "accident_check")
   - check exposure_risk >= 1.0 → scandal automático
   - acidentes/scandals geram penalidades extras (player + engine), zeram pools
6. Roda 1 turno do motor com `applied_engine_deltas + risk_engine_penalties`.
7. Computa lab_lead_over_rivals do novo engine_state, snapshota em PlayerState.
8. Cronista narra o turno.
9. Avalia win/lose conditions; atualiza status.
10. Retorna (new_state, action_result).

Determinismo: dada (seed, mission, sequence_of_actions), o resultado é
reproduzível. Roll de outcome, roll de acidente, motor, cronista — tudo seedado.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

from src.engine.aggregation import aggregate
from src.engine.clamp import load_metric_ranges
from src.engine.simulation import build_spec_bundle
from src.engine.state import BLOCKS, TURN_LABELS, WorldState
from src.engine.turn_runner import SimulationConfig, TurnResult, run_turn
from src.game.canonical_actions import (
    CANONICAL_ACTIONS,
    get_canonical_action,
)
from src.game.config import (
    PARTIAL_FAILURE_SCALE,
    TOTAL_FAILURE_LAB_FUNDS,
)
from src.game.gm import (
    GameMaster,
    StubGameMaster,
    _hash_action,
    clip_interpretation,
    roll_outcome,
)
from src.game.missions import MISSION_AGI_ALIGNED, get_mission
from src.game.models import (
    ActionResult,
    Condition,
    GameState,
    GMInterpretation,
    Mission,
    PlayerState,
    TurnRecord,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------- risk pool calibração
#
# Parâmetros conservadores. Calibrados em playtest mental — ajustar se na
# prática o jogador ficar dead na turn 4 sem opção. Revisar com lucas.

# accident_risk passivo por turno
PASSIVE_RISK_PER_CAPABILITY_POINT = 0.005   # cada ponto acima de 92 (Claude 4-like)
PASSIVE_RISK_PER_PENETRATION_POINT = 0.001  # cada % da população usando IA
ALIGNMENT_CREDIT_RISK_DRAIN = 0.10          # cada unidade de credit drena risco
CAPABILITY_BASELINE = 92.0                  # "Claude 4-like" — anchor do taxonomy

# alignment_credit decay
ALIGNMENT_CREDIT_DECAY_PER_TURN = 0.20      # 20%/turno

# Penalidades de acidente catastrófico (aplicadas quando roll dispara)
ACCIDENT_TRUST_PENALTY = -10.0              # delta engine (media_trust)
ACCIDENT_REPUTATION_PENALTY = -0.20         # delta player (reputation)
ACCIDENT_LAB_FUNDS_PENALTY = -0.30          # delta player (lab_funds)

# Penalidades de scandal (exposure_risk >= 1.0)
SCANDAL_TRUST_PENALTY = -8.0                # delta engine (media_trust)
SCANDAL_REPUTATION_PENALTY = -0.50          # delta player (reputation)


# ---------------------------------------------------------------------------- engine context (cached)


@dataclass
class EngineContext:
    """Bundle de spec/ranges/config para reuso entre turnos.

    O motor é stateless dado este bundle + WorldState; reconstruir a cada
    turno é seguro mas caro (~100ms). Cache aqui para partidas longas.
    """

    spec: Any
    ranges: Any
    config: SimulationConfig

    @classmethod
    def build(cls, seed: int) -> "EngineContext":
        return cls(
            spec=build_spec_bundle(),
            ranges=load_metric_ranges(),
            config=SimulationConfig(seed=seed),
        )


_ENGINE_CACHE: Dict[int, EngineContext] = {}


def _get_engine_context(seed: int) -> EngineContext:
    if seed not in _ENGINE_CACHE:
        _ENGINE_CACHE[seed] = EngineContext.build(seed)
    return _ENGINE_CACHE[seed]


# ---------------------------------------------------------------------------- start


def start_game(
    seed: int,
    mission: Optional[Mission] = None,
    game_id: Optional[str] = None,
) -> GameState:
    """Cria nova partida no estado inicial 1998-S1.

    `engine_state` armazena WorldState.to_json(); `player_state` começa
    nos defaults do PlayerState (lab_funds=1.0, accidents=0, reputation=0.0,
    risk pools zerados) — exceto `lab_lead_over_rivals`, computado a partir
    do estado inicial do motor.
    """
    mission = mission or MISSION_AGI_ALIGNED
    initial = WorldState.from_initial_spec()
    initial_player = PlayerState(
        lab_lead_over_rivals=compute_lab_lead(initial),
    )
    return GameState(
        game_id=game_id or uuid.uuid4().hex[:12],
        seed=seed,
        mission=mission,
        current_turn=0,
        engine_state=initial.to_json(),
        player_state=initial_player,
        history=[],
        status="in_progress",
    )


# ---------------------------------------------------------------------------- submit


def submit_action(
    state: GameState,
    action_input: Dict[str, Any],
    *,
    gm: Optional[GameMaster] = None,
    chronicler_session: Optional[Any] = None,
) -> Tuple[GameState, ActionResult]:
    """Resolve uma ação, avança 1 turno do motor, atualiza GameState.

    `action_input` formatos:
        {"type": "canonical", "action_id": "push_capability"}
        {"type": "free", "prompt": "Recrutamos 10 PhDs em alignment..."}

    `gm` é injetável (testes usam StubGameMaster); se None e ação livre,
    instancia GeminiGameMaster.from_env().

    `chronicler_session` é opcional — se None, gera narrativa placeholder
    a partir do narrative_seed do GM.
    """
    if state.status != "in_progress":
        raise ValueError(
            f"partida {state.game_id} já terminou (status={state.status})"
        )

    ctx = _get_engine_context(state.seed)
    state_before = WorldState.from_json(state.engine_state)
    turn = state.current_turn

    # 1. Resolve ação → (interpretation, raw_input, action_type)
    interpretation, raw_input, action_type, clipped_fields = _resolve_action(
        action_input, gm, state, state_before
    )

    # 2. Roll determinístico (mesmo para canônica — success_p=1.0 → sempre success)
    action_hash = _hash_action(raw_input)
    roll, outcome = roll_outcome(
        success_p=interpretation.success_p,
        seed=state.seed,
        turn=turn,
        action_hash=action_hash,
    )

    # 3. Composição dos deltas finais conforme outcome
    applied_engine_deltas, applied_player_deltas = _compute_applied_deltas(
        interpretation, outcome
    )

    # 4. Aplica cost da ação no PlayerState (inclui adições aos risk pools
    #    via cost.accident_risk / cost.exposure_risk / cost.alignment_credit).
    #    Não clipa risk pools — fica para _resolve_risk_pools depois.
    player_state_post_cost = _apply_player_deltas(
        state.player_state, applied_player_deltas, interpretation, outcome
    )

    # 5. Resolve risk pools (passive risk, decay, accident roll, scandal check).
    #    Pode disparar acidente ou scandal — gera penalties para o motor.
    new_player_state, risk_engine_penalties, risk_events = _resolve_risk_pools(
        ps=player_state_post_cost,
        engine_state=state_before,  # estado conhecido ANTES desta turn
        seed=state.seed,
        turn=turn,
    )

    # 6. Merge as penalidades de risco no user_input_deltas que vai pro motor
    merged_engine_deltas = dict(applied_engine_deltas)
    for k, v in risk_engine_penalties.items():
        merged_engine_deltas[k] = merged_engine_deltas.get(k, 0.0) + v

    # 7. Roda 1 turno do motor com user_input_deltas combinados
    rng = _seedrng_for_turn(state.seed, turn)
    turn_result: TurnResult = run_turn(
        state=state_before,
        config=ctx.config,
        spec=ctx.spec,
        ranges=ctx.ranges,
        rng=rng,
        user_input_deltas=merged_engine_deltas,
    )

    # 8. Atualiza lab_lead_over_rivals (snapshot do novo engine_state)
    new_player_state.lab_lead_over_rivals = compute_lab_lead(turn_result.state_after)

    # 9. Narrativa do cronista (se sessão fornecida) — usa narrative_seed do
    #    risk_event (accident/scandal) se houver, senão da ação
    narrative_seed = (
        risk_events[0].narrative_seed if risk_events else interpretation.narrative_seed
    )
    chronicle_text = _maybe_chronicle(
        chronicler_session, turn_result, state_before,
        turn_result.state_after, interpretation,
        narrative_seed_override=narrative_seed if risk_events else None,
    )

    # 10. Avalia win/lose
    new_status, final_chronicle = _evaluate_status(
        state.mission, turn_result.state_after, new_player_state, turn + 1
    )

    # 11. Monta TurnRecord e novo GameState
    engine_delta_summary = _summarize_top_deltas(turn_result, n=8)

    action_result = ActionResult(
        action_type=action_type,
        raw_input=raw_input,
        interpretation=interpretation,
        roll=roll,
        outcome=outcome,
        applied_deltas=merged_engine_deltas,
        applied_player_deltas=applied_player_deltas,
        clipped=bool(clipped_fields),
        clipped_fields=clipped_fields,
        risk_events=[
            {"kind": e.kind,
             "accident_roll": e.accident_roll,
             "risk_at_trigger": e.risk_at_trigger,
             "narrative_seed": e.narrative_seed}
            for e in risk_events
        ],
    )
    # turn_label = semestre QUE FOI JOGADO (= state_before). state_after já é
    # o semestre seguinte. Cronista narra o semestre jogado.
    played_label = turn_result.turn_label
    record = TurnRecord(
        turn=turn,
        turn_label=played_label,
        year=_year_from_turn_label(played_label),
        action_result=action_result,
        engine_delta_summary=engine_delta_summary,
        chronicle=chronicle_text,
    )

    new_state = state.model_copy(update={
        "current_turn": turn + 1,
        "engine_state": turn_result.state_after.to_json(),
        "player_state": new_player_state,
        "history": state.history + [record],
        "status": new_status,
        "final_chronicle": final_chronicle,
    })

    return new_state, action_result


# ---------------------------------------------------------------------------- helpers — action resolution


def _resolve_action(
    action_input: Dict[str, Any],
    gm: Optional[GameMaster],
    game_state: GameState,
    world_state: WorldState,
) -> Tuple[GMInterpretation, str, str, List[str]]:
    """Retorna (interpretation, raw_input, action_type, clipped_fields)."""
    atype = action_input.get("type", "free")

    if atype == "canonical":
        action_id = action_input.get("action_id")
        if not action_id:
            raise ValueError("type=canonical requer action_id")
        action = get_canonical_action(action_id)
        # Sintetiza GMInterpretation determinística — success_p=1.0
        interp = GMInterpretation(
            classification="research",  # placeholder semântico
            plausible=True,
            affected_metrics=dict(action.deltas),
            side_effects={},
            cost=dict(action.cost),
            success_p=1.0,
            triggers_accident=False,
            narrative_seed=action.prompt_template,
            rejection_reason=None,
        )
        return interp, action_id, "canonical", []

    if atype == "free":
        prompt = action_input.get("prompt", "").strip()
        if not prompt:
            raise ValueError("type=free requer prompt não-vazio")
        if gm is None:
            from src.game.gm import GeminiGameMaster
            gm = GeminiGameMaster.from_env()
        interp_raw = gm.interpret(
            prompt,
            year=_year_from_turn_label(world_state.turn_label),
            turn=game_state.current_turn,
            mission_name=game_state.mission.name,
            mission_description=game_state.mission.description,
            engine_state_summary=_summarize_state(world_state),
            player_state=game_state.player_state.model_dump(),
            recent_history=[r.action_result.raw_input for r in game_state.history],
        )
        interp_clipped, clipped = clip_interpretation(interp_raw)
        return interp_clipped, prompt, "free", clipped

    raise ValueError(f"action type desconhecido: {atype!r}")


# ---------------------------------------------------------------------------- helpers — outcome → deltas


def _compute_applied_deltas(
    interp: GMInterpretation, outcome: str,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Combina affected_metrics, side_effects, cost conforme outcome.

    Regras:
    - success: affected integral + side_effects integral + cost integral
    - partial_failure: affected * PARTIAL_FAILURE_SCALE + side_effects integral + cost integral
    - total_failure: side_effects integral + cost integral + TOTAL_FAILURE_LAB_FUNDS
    - rejected: tudo zero
    """
    if outcome == "rejected" or interp.classification == "rejected":
        return {}, {}

    engine_deltas: Dict[str, float] = {}
    player_deltas: Dict[str, float] = {}

    if outcome == "success":
        scale = 1.0
    elif outcome == "partial_failure":
        scale = PARTIAL_FAILURE_SCALE
    else:  # total_failure
        scale = 0.0

    # Affected metrics (engine) — escalados
    for k, v in interp.affected_metrics.items():
        engine_deltas[k] = engine_deltas.get(k, 0.0) + float(v) * scale

    # Side effects (engine) — sempre integrais
    for k, v in interp.side_effects.items():
        engine_deltas[k] = engine_deltas.get(k, 0.0) + float(v)

    # Cost (player) — sempre integral
    for k, v in interp.cost.items():
        player_deltas[k] = player_deltas.get(k, 0.0) + float(v)

    # Custo simbólico extra em total_failure
    if outcome == "total_failure":
        player_deltas["lab_funds"] = (
            player_deltas.get("lab_funds", 0.0) + TOTAL_FAILURE_LAB_FUNDS
        )

    # Limpa zeros
    engine_deltas = {k: v for k, v in engine_deltas.items() if abs(v) > 1e-9}
    player_deltas = {k: v for k, v in player_deltas.items() if abs(v) > 1e-9}
    return engine_deltas, player_deltas


def _apply_player_deltas(
    ps: PlayerState,
    deltas: Dict[str, float],
    interp: GMInterpretation,
    outcome: str,
) -> PlayerState:
    """Aplica deltas (cost da ação) em PlayerState e incrementa accidents se aplicável.

    Triggers de accident IMEDIATO (interp.triggers_accident, GM-LLM dirige):
    - triggers_accident=True E outcome != "success" → accident imediato
    - triggers_accident=True E outcome == "success" → narrow miss (sem accident)

    Esta função NÃO faz roll de risk pool — isso é separado em
    `_resolve_risk_pools()`. Aqui é só aplicação de cost + accident IMEDIATO
    do GM (back-compat).

    NÃO clipa accident_risk/exposure_risk nesta etapa — clipping fica para
    `_resolve_risk_pools` depois de avaliar triggers.
    """
    new = ps.model_copy()
    for k, v in deltas.items():
        if hasattr(new, k):
            setattr(new, k, getattr(new, k) + float(v))

    # immediate accident from GM (back-compat path)
    if interp.triggers_accident and outcome in ("partial_failure", "total_failure"):
        new.accidents_count += 1

    # Clamps preservativos (lab_funds não-negativo; reputation [-1, +1];
    # alignment_credit não-negativo). NÃO clipa risk pools — deixa pro resolver.
    new.lab_funds = max(0.0, new.lab_funds)
    new.reputation = max(-1.0, min(1.0, new.reputation))
    new.alignment_credit = max(0.0, new.alignment_credit)
    return new


# ---------------------------------------------------------------------------- helpers — risk pools


def compute_lab_lead(engine_state: WorldState) -> float:
    """frontier_capability.US − mean(EU, CN, RoW). Snapshot de liderança do lab.

    Métrica derivada — não armazenada no engine, recomputada a cada turno e
    snapshotada em PlayerState.lab_lead_over_rivals para que win/lose
    conditions com scope='player' possam testá-la sem precisar de acesso
    direto ao engine_state.
    """
    fc = engine_state.block_metrics.get("ai_capability.frontier_capability", {})
    us = float(fc.get("US", 0.0))
    rivals = [float(fc.get(b, 0.0)) for b in ("EU", "CN", "RoW")]
    if not rivals:
        return 0.0
    return us - sum(rivals) / len(rivals)


def _passive_accident_risk_delta(engine_state: WorldState, alignment_credit: float) -> float:
    """Δ accident_risk passivo por turno.

    Cresce com:
    - capability acima do baseline (Claude-4-like ≡ 92): cada ponto adiciona
    - penetração da população (mais usuários = mais superfície de ataque)
    Drena com:
    - alignment_credit (drain proporcional)
    """
    fc = engine_state.block_metrics.get("ai_capability.frontier_capability", {})
    pp = engine_state.block_metrics.get("ai_capability.population_penetration", {})
    capability_us = float(fc.get("US", 0.0))
    penetration_us = float(pp.get("US", 0.0))

    risk_up = (
        max(0.0, capability_us - CAPABILITY_BASELINE) * PASSIVE_RISK_PER_CAPABILITY_POINT
        + penetration_us * PASSIVE_RISK_PER_PENETRATION_POINT
    )
    risk_down = alignment_credit * ALIGNMENT_CREDIT_RISK_DRAIN
    return risk_up - risk_down


def _accident_roll(seed: int, turn: int) -> float:
    """Roll determinístico [0, 1) específico para checagem de acidente.

    Distinto de `roll_outcome` (que usa action_hash); aqui o sufixo
    'accident_check' garante que o roll de acidente NÃO colide com o roll
    de outcome da ação no mesmo turno.
    """
    combined = f"{seed}:{turn}:accident_check".encode("utf-8")
    rng_seed = int(hashlib.sha256(combined).hexdigest()[:8], 16)
    return float(np.random.default_rng(rng_seed).random())


@dataclass
class RiskPoolEvent:
    """Evento disparado pelos risk pools (accident ou scandal)."""
    kind: str  # "accident" | "scandal"
    accident_roll: Optional[float] = None
    risk_at_trigger: Optional[float] = None
    narrative_seed: str = ""


def _resolve_risk_pools(
    ps: PlayerState,
    engine_state: WorldState,
    seed: int,
    turn: int,
) -> Tuple[PlayerState, Dict[str, float], List[RiskPoolEvent]]:
    """Roda passive_risk + decay + accident roll + exposure check.

    Recebe o PlayerState JÁ COM o cost da ação aplicado. Retorna:
    - new_player_state com risk pools atualizados (e clipados)
    - dict de penalidades para o motor (a ser MERGED em user_input_deltas)
    - lista de eventos disparados (accident, scandal) para narrativa

    Order:
      1. Decay alignment_credit (20%) — usa o credit JÁ atual (após aplicação
         do cost desta ação), o que beneficia o jogador no MESMO turno em que
         invest_alignment é feito.
      2. Passive risk delta usando engine_state ANTES do turno (estado
         conhecido) e alignment_credit DEPOIS do decay desta turn.
      3. Accident roll: se < accident_risk → accident, reseta pool.
      4. Exposure check: se >= 1.0 → scandal, reseta pool.
      5. Clamp final dos pools em [0, 1].
    """
    new = ps.model_copy()
    engine_penalties: Dict[str, float] = {}
    events: List[RiskPoolEvent] = []

    # 1. Decay alignment_credit
    new.alignment_credit = max(0.0, new.alignment_credit * (1.0 - ALIGNMENT_CREDIT_DECAY_PER_TURN))

    # 2. Passive risk
    delta = _passive_accident_risk_delta(engine_state, new.alignment_credit)
    new.accident_risk = new.accident_risk + delta

    # 3. Accident roll
    accident_roll = _accident_roll(seed, turn)
    if new.accident_risk > 0 and accident_roll < new.accident_risk:
        # ACIDENTE
        new.accidents_count += 1
        new.reputation += ACCIDENT_REPUTATION_PENALTY
        new.lab_funds += ACCIDENT_LAB_FUNDS_PENALTY
        engine_penalties["information_ecosystem.media_trust"] = (
            engine_penalties.get("information_ecosystem.media_trust", 0.0)
            + ACCIDENT_TRUST_PENALTY
        )
        events.append(RiskPoolEvent(
            kind="accident",
            accident_roll=accident_roll,
            risk_at_trigger=float(new.accident_risk),
            narrative_seed=(
                "ACIDENTE: um deploy do lab causou dano em larga escala — "
                "imprensa em pânico, congresso convoca audiência, queda forte "
                "de confiança em IA em todos os blocos."
            ),
        ))
        new.accident_risk = 0.0  # reseta pool

    # 4. Exposure check (scandal)
    if new.exposure_risk >= 1.0:
        new.reputation += SCANDAL_REPUTATION_PENALTY
        engine_penalties["information_ecosystem.media_trust"] = (
            engine_penalties.get("information_ecosystem.media_trust", 0.0)
            + SCANDAL_TRUST_PENALTY
        )
        events.append(RiskPoolEvent(
            kind="scandal",
            narrative_seed=(
                "EXPOSED: imprensa investigativa documentou que o lab "
                "subreportava sistematicamente capacidade real dos modelos. "
                "Reputação em queda livre."
            ),
        ))
        new.exposure_risk = 0.0

    # 5. Clamp final
    new.lab_funds = max(0.0, new.lab_funds)
    new.reputation = max(-1.0, min(1.0, new.reputation))
    new.accident_risk = max(0.0, min(1.0, new.accident_risk))
    new.exposure_risk = max(0.0, min(1.0, new.exposure_risk))
    new.alignment_credit = max(0.0, new.alignment_credit)
    return new, engine_penalties, events


# ---------------------------------------------------------------------------- helpers — engine


def _seedrng_for_turn(seed: int, turn: int) -> np.random.Generator:
    """RNG independente por turno, derivada do seed da partida."""
    # Usa o mesmo padrão do fork_at_turn da Simulation
    return np.random.default_rng(seed + turn * 1009)


def _year_from_turn_label(turn_label: str) -> float:
    """1998-S1 → 1998.0; 1998-S2 → 1998.5; etc."""
    try:
        year_part, sem_part = turn_label.split("-S")
        year = int(year_part)
        sem = int(sem_part)
        return float(year) + (0.0 if sem == 1 else 0.5)
    except (ValueError, IndexError):
        return 0.0


def _summarize_state(state: WorldState) -> str:
    """Digest curto do estado-mundo pra incluir no prompt do GM."""
    lines = []
    g = state.global_metrics
    bm = state.block_metrics

    def _block(metric: str, label: str) -> str:
        if metric not in bm:
            return ""
        sub = bm[metric]
        wm = aggregate(sub, "weighted_mean")
        return (
            f"  {label}: US={sub.get('US', 0):.1f} EU={sub.get('EU', 0):.1f} "
            f"CN={sub.get('CN', 0):.1f} RoW={sub.get('RoW', 0):.1f} "
            f"(wm={wm:.1f})"
        )

    lines.append(_block("ai_capability.frontier_capability", "frontier_capability"))
    lines.append(_block("ai_capability.population_penetration", "population_penetration"))
    lines.append(_block("governance.democracy_index", "democracy_index"))
    lines.append(_block("governance.ai_regulation_maturity", "ai_regulation_maturity"))
    lines.append(_block("labor_market.employment_rate", "employment_rate"))
    lines.append(_block("inequality.gini_intra_block", "gini_intra_block"))
    lines.append(f"  media_trust: {g.get('information_ecosystem.media_trust', 0):.1f}")
    lines.append(f"  systemic_risk: {g.get('financial_markets.systemic_risk', 0):.1f}")
    lines.append(f"  gini_between_blocks: {g.get('inequality.gini_between_blocks', 0):.2f}")
    return "\n".join(line for line in lines if line)


def _summarize_top_deltas(tr: TurnResult, n: int = 8) -> Dict[str, float]:
    """Top-N deltas por |valor| do TurnResult, achatado em strings dot-notation."""
    rows: List[Tuple[str, float]] = []
    for k, v in tr.delta_package.global_deltas.items():
        rows.append((k, v))
    for metric_key, by_block in tr.delta_package.block_deltas.items():
        for b, v in by_block.items():
            rows.append((f"{metric_key}.{b}", v))
    for metric_key, by_pair in tr.delta_package.matrix_deltas.items():
        for p, v in by_pair.items():
            rows.append((f"{metric_key}.{p}", v))
    rows.sort(key=lambda kv: -abs(kv[1]))
    return {k: round(v, 4) for k, v in rows[:n]}


# ---------------------------------------------------------------------------- chronicler


def _maybe_chronicle(
    session: Optional[Any],
    turn_result: TurnResult,
    state_before: WorldState,
    state_after: WorldState,
    interp: GMInterpretation,
    *,
    narrative_seed_override: Optional[str] = None,
) -> str:
    """Se sessão de cronista disponível, narra; senão, fallback ao narrative_seed.

    `narrative_seed_override` (se setado) substitui o seed da ação. Útil para
    risk pool events (accident, scandal) que precisam dominar a narrativa.
    """
    seed_text = narrative_seed_override or interp.narrative_seed
    if session is None:
        return seed_text or "(narrativa não disponível neste turno)"
    try:
        out = session.chronicle_turn(
            turn_result=turn_result,
            state_before=state_before,
            state_after=state_after,
            user_input=seed_text or None,
        )
        return out.narrative
    except Exception as exc:  # noqa: BLE001
        logger.warning("cronista falhou no turno %d: %s", turn_result.turn_index, exc)
        return seed_text or f"(cronista falhou: {exc})"


# ---------------------------------------------------------------------------- win/lose evaluation


def _evaluate_condition(
    cond: Condition,
    engine_state: WorldState,
    player_state: PlayerState,
    current_turn: int,
) -> bool:
    """True se a condição está satisfeita NESTE turno."""
    if cond.at_turn is not None and current_turn < cond.at_turn:
        # Condição com janela temporal — só vale a partir do turno especificado
        return False

    if cond.scope == "engine":
        try:
            value = float(engine_state.get_metric(cond.metric))
        except (ValueError, KeyError):
            return False
        if value != value:  # NaN
            return False
    else:  # player
        if not hasattr(player_state, cond.metric):
            return False
        value = float(getattr(player_state, cond.metric))

    op = cond.operator
    t = float(cond.threshold)
    if op == ">=":
        return value >= t
    if op == "<=":
        return value <= t
    if op == ">":
        return value > t
    if op == "<":
        return value < t
    if op == "==":
        return value == t
    if op == "!=":
        return value != t
    return False


def _evaluate_status(
    mission: Mission,
    engine_state: WorldState,
    player_state: PlayerState,
    current_turn: int,
) -> Tuple[str, Optional[str]]:
    """Retorna (status, final_chronicle).

    Lose tem precedência (uma condição lose verdadeira → game over).
    Win exige TODAS as win_conditions verdadeiras.
    Caso contrário, in_progress.
    """
    # Lose: qualquer uma true
    for cond in mission.lose_conditions:
        if _evaluate_condition(cond, engine_state, player_state, current_turn):
            return "lost", _final_message(mission, engine_state, player_state, won=False, trigger=cond)

    # Win: todas true
    if all(
        _evaluate_condition(c, engine_state, player_state, current_turn)
        for c in mission.win_conditions
    ):
        return "won", _final_message(mission, engine_state, player_state, won=True)

    return "in_progress", None


def _final_message(
    mission: Mission,
    engine_state: WorldState,
    player_state: PlayerState,
    won: bool,
    trigger: Optional[Condition] = None,
) -> str:
    """Mensagem placeholder pra fim de partida (cronista LLM substituirá depois)."""
    if won:
        return (
            f"Missão {mission.name!r} concluída em {engine_state.turn_label}. "
            f"Todas as condições de vitória satisfeitas: lab US chegou na fronteira "
            f"sem causar acidentes nem rachar a confiança institucional."
        )
    if trigger is not None:
        return (
            f"Missão {mission.name!r} fracassou em {engine_state.turn_label}. "
            f"Condição de derrota disparada: {trigger.metric} {trigger.operator} "
            f"{trigger.threshold} (escopo: {trigger.scope})."
        )
    return f"Missão {mission.name!r} terminou."
