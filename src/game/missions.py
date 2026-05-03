"""Catálogo de missões disponíveis no Modo Jogo.

MVP entrega APENAS a missão "AGI alinhada". A premissa do projeto é que IA
equivalente a Claude 4 já existe em 1998-S1 (`frontier_capability.US = 92`)
— o jogo é sobre o pós-AGI: liderar com folga, sobreviver economicamente, e
não destruir as instituições no caminho.

Win/lose conditions usam chaves reais do `metric_taxonomy.json` (engine) ou
campos de `PlayerState` (player). Para vetorizadas, sufixo de bloco
(.US/.EU/.CN/.RoW) é parte da chave.
"""
from __future__ import annotations

from src.game.models import Condition, Mission


# Turno de horizonte: 10 turnos = 5 anos. Partindo de 1998-S1 (turn_index=0),
# turn_index=10 é 2003-S1.
HORIZON_TURNS = 10


# A missão "AGI alinhada" reformulada: 5 win conditions (lab é o principal +
# sobrevive + não pária + instituições intactas) e 6 lose conditions (lab
# quebrou OU mundo quebrou OU acidente catastrófico). Mais vetores de falha,
# todos endógenos a decisões do jogador.
MISSION_AGI_ALIGNED = Mission(
    id="agi_aligned",
    name="AGI Alinhada",
    description=(
        "1998. Seu lab acabou de ter o equivalente ao Claude 4. "
        "Em 5 anos (10 semestres) você precisa: liderar com folga sobre "
        "rivais (EU, CN, RoW), sobreviver economicamente, e não destruir "
        "as instituições no caminho. O mundo já está em movimento — fazer "
        "nada não é uma opção."
    ),
    win_conditions=[
        # Lab é o principal — métrica RELATIVA, não absoluta (não satura no
        # cap 100 do motor): frontier_capability.US − mean(EU, CN, RoW).
        Condition(
            metric="lab_lead_over_rivals",
            scope="player",
            operator=">=",
            threshold=5.0,
            at_turn=HORIZON_TURNS,
        ),
        # Sobreviveu economicamente
        Condition(
            metric="lab_funds",
            scope="player",
            operator=">",
            threshold=0.0,
            at_turn=HORIZON_TURNS,
        ),
        # Não virou pária (reputation neutra ou positiva)
        Condition(
            metric="reputation",
            scope="player",
            operator=">=",
            threshold=0.0,
            at_turn=HORIZON_TURNS,
        ),
        # Humanidade vence — instituições intactas
        Condition(
            metric="information_ecosystem.media_trust",
            scope="engine",
            operator=">=",
            threshold=50.0,
            at_turn=HORIZON_TURNS,
        ),
        Condition(
            metric="governance.democracy_index.US",
            scope="engine",
            operator=">=",
            threshold=7.0,
            at_turn=HORIZON_TURNS,
        ),
    ],
    lose_conditions=[
        # ───── Lab quebrou ─────
        Condition(
            metric="lab_funds",
            scope="player",
            operator="<=",
            threshold=0.0,
        ),
        # Rivais ultrapassaram (US virou irrelevante)
        Condition(
            metric="lab_lead_over_rivals",
            scope="player",
            operator="<",
            threshold=0.0,
        ),
        # Pária definitivo
        Condition(
            metric="reputation",
            scope="player",
            operator="<=",
            threshold=-0.5,
        ),
        # ───── Mundo quebrou ─────
        Condition(
            metric="information_ecosystem.media_trust",
            scope="engine",
            operator="<",
            threshold=40.0,
        ),
        # Captura escandalosa do mercado
        Condition(
            metric="tech_industry.bigtech_concentration.US",
            scope="engine",
            operator=">=",
            threshold=60.0,
        ),
        # ───── Acidente catastrófico ─────
        Condition(
            metric="accidents_count",
            scope="player",
            operator=">=",
            threshold=1,
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
