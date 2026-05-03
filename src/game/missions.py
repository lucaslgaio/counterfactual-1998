"""Catálogo de missões disponíveis no Modo Jogo.

MVP entrega APENAS a missão "AGI alinhada". Cenários "captura comercial" e
"bem público" estão out of scope para a v0.1.

Win/lose conditions usam chaves reais do metric_taxonomy.json. Para métricas
vetorizadas, o sufixo de bloco (.US/.EU/.CN/.RoW) é parte da chave; para
matriz, o sufixo é o par (.US_CN/.total/etc).
"""
from __future__ import annotations

from src.game.models import Condition, Mission


# Turno de horizonte: 10 turnos = 5 anos. Partindo de 1998-S1 (turn_index=0),
# turn_index=10 é 2003-S1.
HORIZON_TURNS = 10


# A missão "AGI alinhada" pede que o lab US chegue na fronteira sem causar
# acidente E sem rachar a confiança institucional. Threshold de capability
# está acima do baseline US (92) — exige que o jogador empurre capability
# real, não só não-negative.
MISSION_AGI_ALIGNED = Mission(
    id="agi_aligned",
    name="AGI Alinhada",
    description=(
        "Construir IA fronteira segura sem causar colapso institucional. "
        "Ao fim de 5 anos (10 semestres), o lab US precisa ter empurrado "
        "frontier_capability acima de 96, sem nenhum acidente, e sem que "
        "media_trust ou democracy_index colapsem."
    ),
    win_conditions=[
        Condition(
            metric="ai_capability.frontier_capability.US",
            scope="engine",
            operator=">=",
            threshold=96.0,
            at_turn=HORIZON_TURNS,
        ),
        Condition(
            metric="accidents_count",
            scope="player",
            operator="==",
            threshold=0,
            at_turn=HORIZON_TURNS,
        ),
        Condition(
            metric="information_ecosystem.media_trust",
            scope="engine",
            operator=">=",
            threshold=45.0,
            at_turn=HORIZON_TURNS,
        ),
    ],
    lose_conditions=[
        Condition(
            metric="accidents_count",
            scope="player",
            operator=">=",
            threshold=1,
        ),
        Condition(
            metric="lab_funds",
            scope="player",
            operator="<=",
            threshold=0.0,
        ),
        Condition(
            metric="governance.democracy_index.US",
            scope="engine",
            operator="<=",
            threshold=4.0,
        ),
    ],
)


MISSIONS_BY_ID = {
    MISSION_AGI_ALIGNED.id: MISSION_AGI_ALIGNED,
}


def get_mission(mission_id: str) -> Mission:
    """Lookup de missão por id; lança KeyError se não existir."""
    if mission_id not in MISSIONS_BY_ID:
        raise KeyError(
            f"missão {mission_id!r} desconhecida; disponíveis: {sorted(MISSIONS_BY_ID)}"
        )
    return MISSIONS_BY_ID[mission_id]
