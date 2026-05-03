"""Catálogo das 5 ações canônicas — sugestões/templates de ação.

Cada ação canônica define:
- prompt_template: prosa que pré-preenche o textarea no frontend
- deltas: dict metric_key -> delta (formato user_input_deltas do motor)
- cost: dict player_state_field -> delta (negativo gasta, positivo ganha)

Magnitudes calibradas conservadoramente, na faixa low/medium do DAG. As
chaves de métrica seguem o metric_taxonomy real. Ações canônicas NÃO passam
pelo GM-LLM — são determinísticas, success_p efetivo = 1.0.

# TODO: revisar com lucas — magnitudes atuais foram escolhidas pela banda
# medium-conservative. Pode-se afinar contra confidence ranges das edges
# correspondentes do DAG após primeiros playtests.
"""
from __future__ import annotations

from typing import Dict

from src.game.models import CanonicalAction


PUSH_CAPABILITY = CanonicalAction(
    id="push_capability",
    label="Acelerar pesquisa de fronteira",
    prompt_template=(
        "Investimos pesado em escala de compute e contratação de pesquisadores "
        "top-tier para empurrar capability bruta neste semestre. Sem comunicação "
        "pública agressiva — foco interno em P&D."
    ),
    description="Sobe frontier_capability.US forte. Custa lab_funds. Sem efeito direto em trust.",
    deltas={
        "ai_capability.frontier_capability.US": +0.8,
        "science_rd.breakthroughs_per_year.US": +0.2,
    },
    cost={"lab_funds": -0.10},
)


PUBLISH_OPEN = CanonicalAction(
    id="publish_open",
    label="Publicar pesquisa em código aberto",
    prompt_template=(
        "Publicamos os pesos do nosso modelo mais recente e o paper técnico "
        "completo, em open source. Apostamos que difundir capability cria "
        "ecossistema saudável de auditoria e confiança."
    ),
    description=(
        "Distribui capability entre blocos (espalha para EU/CN/RoW). Sobe trust "
        "moderadamente. Pequena perda de vantagem competitiva (US)."
    ),
    deltas={
        "ai_capability.frontier_capability.US": +0.2,
        "ai_capability.frontier_capability.EU": +0.4,
        "ai_capability.frontier_capability.CN": +0.4,
        "ai_capability.frontier_capability.RoW": +0.3,
        "information_ecosystem.media_trust": +1.0,
    },
    cost={"lab_funds": -0.04, "reputation": +0.05},
)


DEPLOY_COMMERCIAL = CanonicalAction(
    id="deploy_commercial",
    label="Lançar produto comercial em larga escala",
    prompt_template=(
        "Lançamos uma versão comercial do nosso modelo para empresas e "
        "consumidores. Foco em receita, escala de uso, e penetração de mercado. "
        "Documentação de segurança limitada — go-to-market acelerado."
    ),
    description=(
        "Sobe population_penetration.US e gera receita. Aumenta automation_exposure "
        "(impacto trabalho) e pode erodir trust se mal-feito."
    ),
    deltas={
        "ai_capability.population_penetration.US": +1.5,
        "labor_market.automation_exposure.US": +0.6,
        "tech_industry.bigtech_concentration.US": +0.5,
        "information_ecosystem.media_trust": -0.5,
    },
    cost={"lab_funds": +0.15, "reputation": -0.03},
)


INVEST_ALIGNMENT = CanonicalAction(
    id="invest_alignment",
    label="Investir pesado em alinhamento e segurança",
    prompt_template=(
        "Direcionamos uma fração grande do orçamento para um time interno de "
        "alinhamento, red-teaming, e auditoria de segurança. Aceitamos atraso "
        "no roadmap de capability em troca de robustez."
    ),
    description=(
        "Aumenta trust e reduz risco de acidente. Custo significativo em "
        "lab_funds. Não move capability."
    ),
    deltas={
        "information_ecosystem.media_trust": +1.5,
        "governance.ai_regulation_maturity.US": +0.3,
    },
    cost={"lab_funds": -0.15, "reputation": +0.08},
)


GOVERNMENT_PARTNERSHIP = CanonicalAction(
    id="government_partnership",
    label="Firmar parceria com governo (regulação)",
    prompt_template=(
        "Aproximamos do executivo americano oferecendo expertise técnica para "
        "estruturar marco regulatório de IA. Aceitamos transparência e auditoria "
        "estatal em troca de legitimidade institucional."
    ),
    description=(
        "Sobe ai_regulation_maturity.US e democracy_index.US. Trade: limita "
        "deployment futuro mas blinda contra colapso institucional."
    ),
    deltas={
        "governance.ai_regulation_maturity.US": +1.2,
        "governance.democracy_index.US": +0.05,
        "information_ecosystem.media_trust": +0.6,
    },
    cost={"lab_funds": -0.06, "reputation": +0.10},
)


CANONICAL_ACTIONS = [
    PUSH_CAPABILITY,
    PUBLISH_OPEN,
    DEPLOY_COMMERCIAL,
    INVEST_ALIGNMENT,
    GOVERNMENT_PARTNERSHIP,
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
