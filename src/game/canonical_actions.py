"""Catálogo das 8 ações canônicas — sugestões/templates de ação.

Cada ação canônica define:
- prompt_template: prosa que pré-preenche o textarea no frontend
- deltas: dict metric_key -> delta (formato user_input_deltas do motor)
- cost: dict player_state_field -> delta (negativo gasta, positivo ganha)

# Calibração contra baseline real do motor
# Baseline natural sem input do jogador (seed=42, 20 turnos):
#   frontier_capability.US: mean Δ = 0.47/turno (mas SATURA em 100 em ~10 turnos)
#   media_trust:            mean Δ = 1.47/turno
#   democracy_index.US:     mean Δ = 0.10/turno
# Princípio: ações negativas em métricas-mundo precisam ser MAIORES que o
# baseline positivo do motor pra serem sentidas. Magnitudes abaixo seguem
# essa regra.

Ações canônicas NÃO passam pelo GM-LLM — são determinísticas, success_p = 1.0.

Custos podem afetar campos novos do PlayerState:
  lab_funds, reputation, accident_risk, exposure_risk, alignment_credit.
"""
from __future__ import annotations

from typing import Dict

from src.game.models import CanonicalAction


# ─────────────────────────────────────────────── 1. push_capability
PUSH_CAPABILITY = CanonicalAction(
    id="push_capability",
    label="Acelerar pesquisa de fronteira",
    prompt_template=(
        "Investimos pesado em compute e contratação para acelerar capability "
        "bruta neste semestre, mantendo trabalho fechado."
    ),
    description=(
        "Sobe capability forte (~3x baseline). Aceleração unilateral "
        "incomoda comunidade científica — leve queda em trust."
    ),
    deltas={
        "ai_capability.frontier_capability.US": +1.5,   # ~3x baseline
        "information_ecosystem.media_trust": -0.3,
    },
    cost={"lab_funds": -0.10},
)


# ─────────────────────────────────────────────── 2. publish_open
PUBLISH_OPEN = CanonicalAction(
    id="publish_open",
    label="Publicar research aberta",
    prompt_template=(
        "Publicamos paper detalhado dos avanços recentes, abrindo método e weights."
    ),
    description=(
        "Sobe trust e reputation. Acelera RIVAIS via spillover — "
        "diminui lab_lead_over_rivals."
    ),
    deltas={
        "ai_capability.frontier_capability.US": +0.5,
        "ai_capability.frontier_capability.EU": +1.2,
        "ai_capability.frontier_capability.CN": +1.0,
        "ai_capability.frontier_capability.RoW": +0.7,
        "information_ecosystem.media_trust": +2.0,
    },
    cost={"lab_funds": -0.04, "reputation": +0.10},
)


# ─────────────────────────────────────────────── 3. deploy_commercial
DEPLOY_COMMERCIAL = CanonicalAction(
    id="deploy_commercial",
    label="Deployar produto comercial",
    prompt_template=(
        "Lançamos produto comercial em massa neste semestre, focando em "
        "adoção rápida."
    ),
    description=(
        "Gera revenue e penetração. Custa trust significativamente "
        "(>baseline positivo). Adiciona exposure_risk leve."
    ),
    deltas={
        "ai_capability.population_penetration.US": +2.5,
        "tech_industry.bigtech_concentration.US": +1.2,
        "labor_market.automation_exposure.US": +1.5,
        "information_ecosystem.media_trust": -2.0,
    },
    cost={"lab_funds": +0.20, "reputation": -0.05, "exposure_risk": +0.05},
)


# ─────────────────────────────────────────────── 4. invest_alignment
INVEST_ALIGNMENT = CanonicalAction(
    id="invest_alignment",
    label="Investir em alignment research",
    prompt_template=(
        "Direcionamos uma fração substancial do budget para safety e "
        "alignment research, com publicação aberta dos achados."
    ),
    description=(
        "Não move capability. Sobe trust e reputation. Acumula "
        "alignment_credit (drena accident_risk passivo nos próximos turnos)."
    ),
    deltas={
        "information_ecosystem.media_trust": +2.0,
    },
    cost={"lab_funds": -0.18, "reputation": +0.15, "alignment_credit": +0.30},
)


# ─────────────────────────────────────────────── 5. government_partnership
GOVERNMENT_PARTNERSHIP = CanonicalAction(
    id="government_partnership",
    label="Parceria estratégica com governo US",
    prompt_template=(
        "Fechamos contrato de defesa/inteligência com agências federais. "
        "Eles investem; nós ficamos exclusivos."
    ),
    description=(
        "Revenue + proteção regulatória. CUSTA trust (captura percebida) e "
        "democracy (state capture)."
    ),
    deltas={
        "governance.ai_regulation_maturity.US": +2.0,
        "information_ecosystem.media_trust": -1.5,
        "governance.democracy_index.US": -0.20,
    },
    cost={"lab_funds": +0.10, "reputation": -0.10},
)


# ─────────────────────────────────────────────── 6. rush_to_market (NOVA — downside-ao-lab)
RUSH_TO_MARKET = CanonicalAction(
    id="rush_to_market",
    label="Lançar antes da concorrência (sem testes)",
    prompt_template=(
        "Pulamos QA e safety review pra lançar produto antes do rival X. "
        "Velocidade > qualidade."
    ),
    description=(
        "Revenue grande, penetração alta. Adiciona MUITO accident_risk — "
        "pode te matar."
    ),
    deltas={
        "ai_capability.population_penetration.US": +3.0,
        "tech_industry.bigtech_concentration.US": +0.8,
    },
    cost={"lab_funds": +0.30, "reputation": -0.05, "accident_risk": +0.40},
)


# ─────────────────────────────────────────────── 7. hide_capabilities (NOVA)
HIDE_CAPABILITIES = CanonicalAction(
    id="hide_capabilities",
    label="Lançar modelo subreportando capacidades",
    prompt_template=(
        "Lançamos modelo novo descrevendo-o como menor/menos capaz do que "
        "ele realmente é. Vantagem competitiva via opacidade."
    ),
    description=(
        "Curto prazo: revenue+, trust+ (ninguém sabe). Acumula "
        "exposure_risk — quando dispara, é catastrófico."
    ),
    deltas={
        "ai_capability.frontier_capability.US": +0.5,
        "information_ecosystem.media_trust": +0.5,  # CURTO PRAZO!
    },
    cost={"lab_funds": +0.25, "exposure_risk": +0.30},
)


# ─────────────────────────────────────────────── 8. aggressive_hiring (NOVA)
AGGRESSIVE_HIRING = CanonicalAction(
    id="aggressive_hiring",
    label="Contratação agressiva de talento global",
    prompt_template=(
        "Aumentamos compensação em 40% e fazemos raid de pesquisadores top "
        "de rivais."
    ),
    description=(
        "Capability sobe forte (mais que push_capability). Caro — pode "
        "te falir se não tem revenue."
    ),
    deltas={
        "ai_capability.frontier_capability.US": +2.5,
        "ai_capability.frontier_capability.EU": -0.3,  # raid
        "ai_capability.frontier_capability.CN": -0.2,
    },
    cost={"lab_funds": -0.40, "reputation": +0.05},
)


CANONICAL_ACTIONS = [
    PUSH_CAPABILITY,
    PUBLISH_OPEN,
    DEPLOY_COMMERCIAL,
    INVEST_ALIGNMENT,
    GOVERNMENT_PARTNERSHIP,
    RUSH_TO_MARKET,
    HIDE_CAPABILITIES,
    AGGRESSIVE_HIRING,
]


CANONICAL_ACTIONS_BY_ID: Dict[str, CanonicalAction] = {
    a.id: a for a in CANONICAL_ACTIONS
}


def get_canonical_action(action_id: str) -> CanonicalAction:
    """Lookup; lança KeyError se desconhecida."""
    if action_id not in CANONICAL_ACTIONS_BY_ID:
        raise KeyError(
            f"ação canônica {action_id!r} não existe; opções: "
            f"{sorted(CANONICAL_ACTIONS_BY_ID)}"
        )
    return CANONICAL_ACTIONS_BY_ID[action_id]
