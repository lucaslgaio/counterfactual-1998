"""Glossário das 24 métricas: descrição, unidade, âncoras e templates de interpretação.

Usado em três lugares:
1. Tela de manual (--manual flag) na intro
2. Formatação de deltas com unidade ao lado
3. Prosa interpretativa no outro
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class MetricInfo:
    cluster: str
    dimension: str
    metric: str
    short_label: str           # nome amigável curto pra tabelas
    description: str           # o que a métrica representa
    unit: str                  # ex: "% da pop", "anos", "GtCO₂/ano", "" pra adimensional
    range_label: str           # ex: "0–100", "0–1"
    anchors: Tuple[Tuple[float, str], ...]  # pontos de referência: (valor, significado)
    template: str              # f-string com {before}, {after}, {delta}, {abs_delta}

    @property
    def key(self) -> str:
        return f"{self.dimension}.{self.metric}"

    def format_delta(self, delta: float) -> str:
        sign = "+" if delta >= 0 else ""
        unit = f" {self.unit}" if self.unit else ""
        return f"{sign}{delta:.2f}{unit}"

    def interpret(self, before: float, after: float) -> str:
        delta = after - before
        return self.template.format(
            before=before,
            after=after,
            delta=delta,
            abs_delta=abs(delta),
        )


# Polaridade: métricas onde "subir" significa piorar do ponto de vista humano.
BAD_WHEN_UP = frozenset({
    "systemic_risk",
    "automation_exposure",
    "global_gini",
    "top1pct_share",
    "active_conflicts",
    "disinformation_level",
    "co2_gt_year",
    "cost_index",
    "bigtech_concentration",
})


METRICS_LIST = [
    # ── Cluster: Tecnologia & IA ────────────────────────────────────────────
    MetricInfo(
        cluster="Tecnologia & IA",
        dimension="ai_capability",
        metric="frontier_capability",
        short_label="capacidade frontier",
        description="Capacidade da IA mais avançada do mundo (raciocínio, código, multimodal).",
        unit="pontos",
        range_label="0–100",
        anchors=(
            (15, "ML clássico, regras"),
            (60, "GPT-3-like, utilidade prática crescente"),
            (92, "Claude 4-like, raciocínio multi-passo, código, multimodal"),
        ),
        template="Fronteira de capacidade da IA: {before:.0f} → {after:.0f} pontos ({delta:+.0f}).",
    ),
    MetricInfo(
        cluster="Tecnologia & IA",
        dimension="ai_capability",
        metric="population_penetration",
        short_label="acesso à IA",
        description="% da população global que usa IA com alguma frequência.",
        unit="pp",
        range_label="0–100",
        anchors=(
            (1, "uso restrito a pesquisadores"),
            (5, "ponto de partida em S1/1998 (big_bang)"),
            (50, "metade do mundo conectada"),
            (90, "uso quase-universal"),
        ),
        template="Acesso à IA: {before:.1f}% → {after:.1f}% da população ({delta:+.1f} pp).",
    ),
    MetricInfo(
        cluster="Tecnologia & IA",
        dimension="tech_industry",
        metric="bigtech_concentration",
        short_label="concentração bigtech",
        description="Concentração de mercado entre as maiores empresas de tecnologia (estilo HHI).",
        unit="pontos",
        range_label="0–100",
        anchors=(
            (10, "mercado fragmentado"),
            (22, "ponto de partida em 1998"),
            (60, "oligopólio claro"),
            (85, "monopólio efetivo de 2-3 atores"),
        ),
        template="Concentração de bigtech (HHI): {before:.1f} → {after:.1f} pontos ({delta:+.1f}).",
    ),
    MetricInfo(
        cluster="Tecnologia & IA",
        dimension="tech_industry",
        metric="tech_employment_share",
        short_label="empregos em tech",
        description="% da força de trabalho global empregada em setores de tecnologia.",
        unit="pp",
        range_label="0–100",
        anchors=(
            (3.1, "ponto de partida em 1998"),
            (8, "tech como setor maduro"),
            (15, "tech absorvendo manufatura/serviços"),
        ),
        template="Empregos em tech: {before:.2f}% → {after:.2f}% da força de trabalho global ({delta:+.2f} pp).",
    ),

    # ── Cluster: Economia ───────────────────────────────────────────────────
    MetricInfo(
        cluster="Economia",
        dimension="financial_markets",
        metric="global_index",
        short_label="índice global de ações",
        description="Índice agregado dos mercados de ações globais. Base 100 em S1/1998.",
        unit="(base 100)",
        range_label="0–10000",
        anchors=(
            (100, "ponto de partida em 1998"),
            (60, "crash severo (-40%)"),
            (250, "alta de longo prazo"),
            (500, "boom histórico"),
        ),
        template="Índice global de ações: {before:.0f} → {after:.0f} ({delta:+.0f} pontos, base 100 em 1998).",
    ),
    MetricInfo(
        cluster="Economia",
        dimension="financial_markets",
        metric="systemic_risk",
        short_label="risco sistêmico",
        description="Risco de falha em cascata no sistema financeiro global.",
        unit="pontos",
        range_label="0–100",
        anchors=(
            (10, "calmaria pós-crise"),
            (35, "ponto de partida em 1998"),
            (70, "tensão alta (subprime 2007)"),
            (90, "colapso iminente (Lehman 2008)"),
        ),
        template="Risco sistêmico financeiro: {before:.1f} → {after:.1f} pontos ({delta:+.1f}).",
    ),
    MetricInfo(
        cluster="Economia",
        dimension="labor_market",
        metric="employment_rate",
        short_label="taxa de emprego",
        description="% da população em idade ativa que está empregada.",
        unit="pp",
        range_label="0–100",
        anchors=(
            (62.8, "ponto de partida em 1998"),
            (55, "recessão profunda"),
            (70, "pleno emprego histórico"),
        ),
        template="Taxa de emprego global: {before:.1f}% → {after:.1f}% ({delta:+.2f} pp).",
    ),
    MetricInfo(
        cluster="Economia",
        dimension="labor_market",
        metric="automation_exposure",
        short_label="empregos em risco de automação",
        description="% dos empregos com risco significativo de serem automatizados nos próximos 10 anos.",
        unit="pp",
        range_label="0–100",
        anchors=(
            (8, "ponto de partida em 1998"),
            (30, "AGI no horizonte, white-collar exposto"),
            (60, "automação massiva"),
        ),
        template="Empregos em risco de automação: {before:.1f}% → {after:.1f}% ({delta:+.1f} pp).",
    ),

    # ── Cluster: Sociedade ──────────────────────────────────────────────────
    MetricInfo(
        cluster="Sociedade",
        dimension="education",
        metric="mean_years_schooling",
        short_label="escolaridade média",
        description="Média global de anos de escolaridade (Barro-Lee/UNESCO).",
        unit="anos",
        range_label="0–25",
        anchors=(
            (7.4, "ponto de partida em 1998"),
            (10, "ensino médio universal"),
            (14, "ensino superior universal"),
        ),
        template="Escolaridade média global: {before:.1f} → {after:.1f} anos ({delta:+.2f}).",
    ),
    MetricInfo(
        cluster="Sociedade",
        dimension="education",
        metric="cost_index",
        short_label="custo da educação",
        description="Índice global de custo de acesso à educação. Base 100 em 1998.",
        unit="(base 100)",
        range_label="0–1000",
        anchors=(
            (100, "ponto de partida em 1998"),
            (50, "educação significativamente mais barata (IA tutor)"),
            (200, "elitização severa"),
        ),
        template="Custo da educação (índice base 100): {before:.0f} → {after:.0f} ({delta:+.1f}).",
    ),
    MetricInfo(
        cluster="Sociedade",
        dimension="inequality",
        metric="global_gini",
        short_label="Gini global",
        description="Coeficiente de Gini de renda em escala global. 0 = igualdade total, 1 = todo o mundo zerado e uma pessoa com tudo.",
        unit="",
        range_label="0–1",
        anchors=(
            (0.69, "ponto de partida em 1998 (extremamente desigual entre países)"),
            (0.55, "mundo significativamente menos desigual"),
            (0.85, "desigualdade catastrófica"),
        ),
        template="Gini global de renda: {before:.3f} → {after:.3f} ({delta:+.3f}).",
    ),
    MetricInfo(
        cluster="Sociedade",
        dimension="inequality",
        metric="top1pct_share",
        short_label="riqueza no topo 1%",
        description="% da riqueza global detida pelo 1% mais rico.",
        unit="pp",
        range_label="0–100",
        anchors=(
            (19, "ponto de partida em 1998"),
            (10, "redistribuição expressiva"),
            (50, "captura oligárquica"),
        ),
        template="Riqueza nas mãos do top 1%: {before:.1f}% → {after:.1f}% ({delta:+.2f} pp).",
    ),

    # ── Cluster: Conhecimento & Saúde ──────────────────────────────────────
    MetricInfo(
        cluster="Conhecimento & Saúde",
        dimension="health",
        metric="life_expectancy",
        short_label="expectativa de vida",
        description="Expectativa média de vida ao nascer, global.",
        unit="anos",
        range_label="0–120",
        anchors=(
            (67, "ponto de partida em 1998"),
            (75, "média 2020s da linha real"),
            (90, "ganhos significativos via medicina assistida por IA"),
        ),
        template="Expectativa de vida global: {before:.1f} → {after:.1f} anos ({delta:+.2f}).",
    ),
    MetricInfo(
        cluster="Conhecimento & Saúde",
        dimension="health",
        metric="diagnostic_accuracy",
        short_label="diagnóstico AI-augmented",
        description="% dos diagnósticos médicos no mundo que são apoiados por IA.",
        unit="pp",
        range_label="0–100",
        anchors=(
            (2, "ponto de partida em 1998 (uso experimental)"),
            (30, "padrão em hospitais de referência"),
            (80, "padrão global"),
        ),
        template="Diagnósticos médicos AI-augmented: {before:.1f}% → {after:.1f}% dos casos ({delta:+.2f} pp).",
    ),
    MetricInfo(
        cluster="Conhecimento & Saúde",
        dimension="science_rd",
        metric="publications_index",
        short_label="publicações científicas",
        description="Índice de publicações científicas anuais. Base 100 em 1998.",
        unit="(base 100)",
        range_label="0–10000",
        anchors=(
            (100, "ponto de partida em 1998"),
            (300, "ciência 3x mais produtiva"),
            (1000, "explosão científica via IA"),
        ),
        template="Publicações científicas (índice base 100): {before:.0f} → {after:.0f} ({delta:+.1f}).",
    ),
    MetricInfo(
        cluster="Conhecimento & Saúde",
        dimension="science_rd",
        metric="breakthroughs_per_year",
        short_label="breakthroughs/ano",
        description="Número de descobertas científicas significativas por ano (estimativa qualitativa).",
        unit="por ano",
        range_label="0–1000",
        anchors=(
            (12, "ponto de partida em 1998"),
            (50, "ritmo acelerado por IA"),
            (200, "AGI fazendo ciência sozinha"),
        ),
        template="Breakthroughs científicos/ano: {before:.0f} → {after:.0f} ({delta:+.1f}).",
    ),

    # ── Cluster: Política ───────────────────────────────────────────────────
    MetricInfo(
        cluster="Política",
        dimension="geopolitics",
        metric="us_china_balance",
        short_label="balança EUA-China",
        description="Balança de poder entre EUA e China. -100 = China hegemônica, +100 = EUA hegemônicos.",
        unit="pontos",
        range_label="-100 a +100",
        anchors=(
            (75, "ponto de partida em 1998 (EUA dominantes)"),
            (0, "paridade"),
            (-50, "China com vantagem clara"),
        ),
        template="Balança EUA-China: {before:.1f} → {after:.1f} pontos ({delta:+.1f}). Negativo = China à frente.",
    ),
    MetricInfo(
        cluster="Política",
        dimension="geopolitics",
        metric="active_conflicts",
        short_label="conflitos armados",
        description="Número de conflitos armados ativos no mundo (>1000 baixas/ano).",
        unit="conflitos",
        range_label="0–200",
        anchors=(
            (38, "ponto de partida em 1998"),
            (20, "mundo significativamente mais pacífico"),
            (80, "fragmentação geopolítica severa"),
        ),
        template="Conflitos armados ativos: {before:.0f} → {after:.0f} ({delta:+.1f}).",
    ),
    MetricInfo(
        cluster="Política",
        dimension="governance",
        metric="democracy_index",
        short_label="índice de democracia",
        description="Índice global de democracia (estilo EIU). 0 = autoritário total, 10 = democracia plena.",
        unit="(0-10)",
        range_label="0–10",
        anchors=(
            (5.5, "ponto de partida em 1998"),
            (7, "maioria democrática consolidada"),
            (3, "recuo autoritário global"),
        ),
        template="Índice global de democracia: {before:.2f} → {after:.2f}/10 ({delta:+.2f}).",
    ),
    MetricInfo(
        cluster="Política",
        dimension="governance",
        metric="ai_regulation_maturity",
        short_label="maturidade da regulação de IA",
        description="Quanto a regulação de IA está consolidada globalmente.",
        unit="pontos",
        range_label="0–100",
        anchors=(
            (0, "ponto de partida em 1998 (não existe ainda)"),
            (40, "marcos como AI Act europeu"),
            (90, "regulação global vinculante"),
        ),
        template="Maturidade da regulação de IA: {before:.1f} → {after:.1f}/100 ({delta:+.2f}).",
    ),

    # ── Cluster: Informação & Ambiente ─────────────────────────────────────
    MetricInfo(
        cluster="Informação & Ambiente",
        dimension="information_ecosystem",
        metric="media_trust",
        short_label="confiança em mídia",
        description="Confiança média do público em mídia tradicional e jornalismo profissional.",
        unit="pontos",
        range_label="0–100",
        anchors=(
            (53, "ponto de partida em 1998"),
            (30, "crise profunda de confiança"),
            (70, "imprensa restaurada como autoridade"),
        ),
        template="Confiança em mídia tradicional: {before:.1f} → {after:.1f} pontos ({delta:+.1f}).",
    ),
    MetricInfo(
        cluster="Informação & Ambiente",
        dimension="information_ecosystem",
        metric="disinformation_level",
        short_label="desinformação",
        description="Nível de desinformação circulando no ecossistema informacional.",
        unit="pontos",
        range_label="0–100",
        anchors=(
            (18, "ponto de partida em 1998"),
            (50, "deepfakes industriais, redes saturadas"),
            (80, "realidade fragmentada"),
        ),
        template="Nível de desinformação: {before:.1f} → {after:.1f} pontos ({delta:+.1f}).",
    ),
    MetricInfo(
        cluster="Informação & Ambiente",
        dimension="energy_climate",
        metric="co2_gt_year",
        short_label="emissões de CO₂",
        description="Emissões globais de CO₂ por ano em GtCO₂.",
        unit="GtCO₂/ano",
        range_label="0–100",
        anchors=(
            (24.4, "ponto de partida em 1998"),
            (10, "trajetória compatível com 1.5°C"),
            (40, "trajetória catastrófica"),
        ),
        template="Emissões globais de CO₂: {before:.1f} → {after:.1f} GtCO₂/ano ({delta:+.2f}).",
    ),
    MetricInfo(
        cluster="Informação & Ambiente",
        dimension="energy_climate",
        metric="renewable_share",
        short_label="renováveis na matriz",
        description="% da matriz energética global que vem de fontes renováveis.",
        unit="pp",
        range_label="0–100",
        anchors=(
            (6, "ponto de partida em 1998 (hidrelétrica + biomassa)"),
            (30, "transição em curso"),
            (70, "matriz majoritariamente limpa"),
        ),
        template="Renováveis na matriz energética: {before:.1f}% → {after:.1f}% ({delta:+.2f} pp).",
    ),
]


METRICS: dict[str, MetricInfo] = {m.key: m for m in METRICS_LIST}


def metrics_by_cluster() -> dict[str, list[MetricInfo]]:
    """Agrupa métricas por cluster preservando a ordem de inserção."""
    out: dict[str, list[MetricInfo]] = {}
    for m in METRICS_LIST:
        out.setdefault(m.cluster, []).append(m)
    return out
