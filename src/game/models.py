"""Modelos Pydantic do Modo Jogo.

Convenções:
- Todas as métricas-mundo (engine) são endereçadas pela chave dot-notation real
  do `metric_taxonomy.json` — por exemplo `ai_capability.frontier_capability.US`
  para uma métrica vetorizada com sufixo de bloco.
- `engine_state` em `GameState` é o `WorldState.to_json()` serializado;
  `player_state` é separado e não entra no motor.
- `applied_deltas` em `ActionResult` reflete EXATAMENTE o que foi enviado como
  `user_input_deltas` ao motor (já com cap/clip/sucesso aplicados).
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------- mission


class Condition(BaseModel):
    """Critério atômico de vitória/derrota.

    Avaliado contra `engine_state` (snapshot serializado do WorldState) ou
    `player_state` conforme `scope`. Para `scope=engine`, a chave deve seguir
    a notação dot do metric_taxonomy (ex.: `ai_capability.frontier_capability.US`,
    `inequality.gini_between_blocks`).
    """

    metric: str
    scope: Literal["engine", "player"]
    operator: Literal[">=", "<=", "==", "!=", ">", "<"]
    threshold: float
    at_turn: Optional[int] = None  # se setado, condição só vale a partir deste turno


class Mission(BaseModel):
    id: str
    name: str
    description: str
    win_conditions: List[Condition]
    lose_conditions: List[Condition]


# ---------------------------------------------------------------------------- canonical actions


class CanonicalAction(BaseModel):
    """Ação canônica — template + deltas predefinidos. NÃO passa por GM-LLM.

    O `prompt_template` é texto natural que pré-preenche o textarea no frontend
    (jogador pode editar antes de submeter, mas se submeter como canonical, o
    backend usa os `deltas`/`cost` predefinidos e ignora edições). Ações livres
    sempre passam por GM.
    """

    id: str
    label: str
    prompt_template: str
    description: str
    deltas: Dict[str, float] = Field(default_factory=dict)
    cost: Dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------- GM


class GMInterpretation(BaseModel):
    """Saída estruturada do GM-LLM para uma ação livre.

    `affected_metrics` e `side_effects` são dicts metric_key -> delta (mesmo
    formato consumido pelo motor como user_input_deltas). `success_p` é a
    probabilidade de sucesso integral; o roll determinístico decide entre
    success / partial_failure / total_failure.

    `triggers_accident` quando true, incrementa `player_state.accidents_count`
    no outcome (independente de magnitude). Use para ações imprudentes/rushed
    que claramente envolveriam risco de acidente — é o gatilho principal de
    derrota no missão "AGI alinhada".
    """

    classification: Literal[
        "research", "deployment", "lobby", "partnership", "comms", "m_and_a", "rejected"
    ]
    plausible: bool
    affected_metrics: Dict[str, float] = Field(default_factory=dict)
    side_effects: Dict[str, float] = Field(default_factory=dict)
    cost: Dict[str, float] = Field(default_factory=dict)
    success_p: float = Field(ge=0.0, le=1.0, default=0.5)
    triggers_accident: bool = False
    narrative_seed: str = ""
    rejection_reason: Optional[str] = None


class ActionResult(BaseModel):
    """Resultado completo da resolução de uma ação.

    `applied_deltas` reflete o que foi efetivamente injetado no motor neste
    turno — INCLUI penalidades de risk pools (accident, scandal) se elas
    dispararam. Use `risk_events` para distinguir o que veio de risk vs ação.

    `risk_events` é uma lista de dicts opacos descrevendo eventos de risk
    pool disparados nesta turn (kind, narrative_seed, etc). Tipicamente 0 ou
    1 evento por turn, mas accident + scandal podem coexistir.
    """

    action_type: Literal["canonical", "free"]
    raw_input: str  # action_id se canônica, prompt do jogador se livre
    interpretation: Optional[GMInterpretation] = None
    roll: float  # 0.0 - 1.0
    outcome: Literal["success", "partial_failure", "total_failure", "rejected"]
    applied_deltas: Dict[str, float] = Field(default_factory=dict)
    applied_player_deltas: Dict[str, float] = Field(default_factory=dict)
    clipped: bool = False
    clipped_fields: List[str] = Field(default_factory=list)
    risk_events: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------- player state


class PlayerState(BaseModel):
    """Estado do lab/CEO. Métricas-jogo, separadas das métricas-mundo.

    Campos persistentes (atualizados a cada turno):
    - lab_funds: tesouro do lab (1.0 = saldo inicial saudável; 0.0 = falência).
    - accidents_count: número de acidentes graves causados pelo lab.
    - reputation: percepção pública/governo do lab. SIGNED [-1.0, +1.0],
      default 0. Negativo = pária (lobby/imprensa hostis); positivo = querido.

    Risk pools (acumulam ao longo da partida):
    - accident_risk: probabilidade [0, 1] de acidente sortado a cada turno.
      Sobe com capability + penetração + ações arriscadas; desce via
      alignment_credit. Reseta para 0 quando dispara um acidente.
    - exposure_risk: estoque [0, 1] de "engano público acumulado".
      NÃO decai sozinho — só sobe ou reseta no scandal. Quando >= 1.0,
      dispara automaticamente um scandal no mesmo turno (penalidades fortes).
    - alignment_credit: estoque positivo gerado por invest_alignment.
      Drena accident_risk passivo. Decai 20%/turno (não é estoque permanente).

    Métricas derivadas (recomputadas a cada turno a partir do engine_state):
    - lab_lead_over_rivals: frontier_capability.US - mean(EU, CN, RoW).
      Snapshot armazenado para que win/lose conditions possam testar via
      scope='player' sem precisar acessar engine_state.
    """

    lab_funds: float = 1.0
    accidents_count: int = 0
    reputation: float = Field(default=0.0, ge=-1.0, le=1.0)
    accident_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    # exposure_risk pode ultrapassar 1.0 transientemente — _resolve_risk_pools
    # checa o threshold (>= 1.0 dispara scandal), depois reseta para 0 e clampa
    # ao range válido [0, 1]. Pydantic só rejeita negativos.
    exposure_risk: float = Field(default=0.0, ge=0.0)
    alignment_credit: float = Field(default=0.0, ge=0.0)
    lab_lead_over_rivals: float = 0.0


# ---------------------------------------------------------------------------- turn record


class TurnRecord(BaseModel):
    """Registro de um turno completo, persistido em GameState.history."""

    turn: int
    turn_label: str
    year: float
    action_result: ActionResult
    engine_delta_summary: Dict[str, float] = Field(default_factory=dict)
    chronicle: str = ""


# ---------------------------------------------------------------------------- game state


class GameState(BaseModel):
    """Estado completo da partida — único objeto persistido entre chamadas.

    `engine_state` é o WorldState.to_json() (3 camadas: global/block/matrix +
    metadata). `player_state` é o PlayerState. `status` muda para won/lost
    quando alguma condição da missão dispara.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    game_id: str
    seed: int
    mission: Mission
    current_turn: int
    engine_state: Dict[str, Any]
    player_state: PlayerState
    history: List[TurnRecord] = Field(default_factory=list)
    status: Literal["in_progress", "won", "lost"] = "in_progress"
    final_chronicle: Optional[str] = None
