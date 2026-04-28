"""Pydantic models para estado, eventos, choques e respostas de turno."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from src.config import SimulationConfig


# =============================================================================
# Dimensões do estado (12 dimensões, 24 métricas)
# =============================================================================


class AICapability(BaseModel):
    frontier_capability: float = Field(ge=0, le=100, description="Capacidade da fronteira de IA (0-100).")
    population_penetration: float = Field(ge=0, le=100, description="% da população usando IA.")


class TechIndustry(BaseModel):
    bigtech_concentration: float = Field(ge=0, le=100, description="HHI de concentração de bigtechs.")
    tech_employment_share: float = Field(ge=0, le=100, description="% da força de trabalho em tech.")


class FinancialMarkets(BaseModel):
    global_index: float = Field(ge=0, le=10000, description="Índice global de ações, base 100 em 1998.")
    systemic_risk: float = Field(ge=0, le=100, description="Risco sistêmico do sistema financeiro.")


class LaborMarket(BaseModel):
    employment_rate: float = Field(ge=0, le=100, description="Taxa de emprego global (%).")
    automation_exposure: float = Field(ge=0, le=100, description="% de empregos em risco de automação.")


class Education(BaseModel):
    mean_years_schooling: float = Field(ge=0, le=25, description="Média global de anos de estudo.")
    cost_index: float = Field(ge=0, le=1000, description="Índice de custo da educação, base 100 em 1998.")


class Inequality(BaseModel):
    global_gini: float = Field(ge=0, le=1, description="Coeficiente de Gini global (renda).")
    top1pct_share: float = Field(ge=0, le=100, description="% da riqueza nos 1% mais ricos.")


class Health(BaseModel):
    life_expectancy: float = Field(ge=0, le=120, description="Expectativa de vida global (anos).")
    diagnostic_accuracy: float = Field(ge=0, le=100, description="% de diagnósticos médicos AI-augmented.")


class ScienceRD(BaseModel):
    publications_index: float = Field(ge=0, le=10000, description="Índice de publicações científicas, base 100 em 1998.")
    breakthroughs_per_year: float = Field(ge=0, le=1000, description="Breakthroughs científicos por ano.")


class Geopolitics(BaseModel):
    us_china_balance: float = Field(ge=-100, le=100, description="-100 = China hegemonic, +100 = US hegemonic.")
    active_conflicts: float = Field(ge=0, le=200, description="Número de conflitos armados ativos.")


class Governance(BaseModel):
    democracy_index: float = Field(ge=0, le=10, description="Índice de democracia (EIU).")
    ai_regulation_maturity: float = Field(ge=0, le=100, description="Maturidade da regulação de IA.")


class InformationEcosystem(BaseModel):
    media_trust: float = Field(ge=0, le=100, description="Confiança em mídia tradicional.")
    disinformation_level: float = Field(ge=0, le=100, description="Nível de desinformação no ecossistema.")


class EnergyClimate(BaseModel):
    co2_gt_year: float = Field(ge=0, le=100, description="Emissões globais de CO2 (GtCO2/ano).")
    renewable_share: float = Field(ge=0, le=100, description="% da matriz energética renovável.")


# =============================================================================
# Estado completo
# =============================================================================


class State(BaseModel):
    turn: str = Field(description="Turno no formato 'YYYY-S1' ou 'YYYY-S2'.")
    config: SimulationConfig
    ai_capability: AICapability
    tech_industry: TechIndustry
    financial_markets: FinancialMarkets
    labor_market: LaborMarket
    education: Education
    inequality: Inequality
    health: Health
    science_rd: ScienceRD
    geopolitics: Geopolitics
    governance: Governance
    information_ecosystem: InformationEcosystem
    energy_climate: EnergyClimate


# =============================================================================
# Eventos e choques
# =============================================================================

EventSeverity = Literal["low", "medium", "high", "critical"]


class HistoricalEvent(BaseModel):
    date: str
    name: str
    severity: EventSeverity
    domain: str


class ExogenousShock(BaseModel):
    name: str
    description: str
    domain: str
    severity: Literal["low", "medium", "high"]


# =============================================================================
# Resposta do LLM por turno
# =============================================================================

EventOutcome = Literal["ocorreu", "alterado", "anulado", "N/A"]


class CausalLink(BaseModel):
    source: str = Field(
        description="Origem da relação causal: nome do evento/choque OU 'dimensao.metrica'.",
    )
    target: str = Field(
        description="Métrica afetada, sempre no formato 'dimensao.metrica'.",
    )
    direction: Literal["up", "down"]


class TurnResponse(BaseModel):
    narrative: str = Field(description="80-200 palavras descrevendo o que aconteceu neste semestre.")
    key_developments: list[str] = Field(min_length=2, max_length=4)
    event_outcome: EventOutcome
    event_outcome_explanation: Optional[str] = None
    deltas: dict[str, float] = Field(default_factory=dict)
    delta_explanations: dict[str, str] = Field(default_factory=dict)
    causal_links: list[CausalLink] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]

    @model_validator(mode="before")
    @classmethod
    def _coerce_delta_list(cls, data: Any) -> Any:
        """Aceita deltas como list[{metric, value, explanation}] ou dict[str, float].

        Gemini retorna deltas como array de objetos pra evitar property names
        com pontos no schema. Aqui separamos os valores numéricos (em `deltas`)
        das explicações curtas (em `delta_explanations`).
        """
        if not isinstance(data, dict):
            return data
        deltas_raw = data.get("deltas")
        if isinstance(deltas_raw, list):
            new_deltas: dict[str, float] = {}
            new_explanations: dict[str, str] = {}
            for item in deltas_raw:
                if not isinstance(item, dict) or "metric" not in item or "value" not in item:
                    continue
                metric = item["metric"]
                new_deltas[metric] = float(item["value"])
                explanation = item.get("explanation", "")
                if explanation:
                    new_explanations[metric] = str(explanation).strip()
            data["deltas"] = new_deltas
            if "delta_explanations" not in data:
                data["delta_explanations"] = new_explanations
        return data


# =============================================================================
# Aplicação de deltas (aditivos, com clamp)
# =============================================================================


DIMENSION_CLASSES: dict[str, type[BaseModel]] = {
    "ai_capability": AICapability,
    "tech_industry": TechIndustry,
    "financial_markets": FinancialMarkets,
    "labor_market": LaborMarket,
    "education": Education,
    "inequality": Inequality,
    "health": Health,
    "science_rd": ScienceRD,
    "geopolitics": Geopolitics,
    "governance": Governance,
    "information_ecosystem": InformationEcosystem,
    "energy_climate": EnergyClimate,
}


def _get_bounds(dim_name: str, metric_name: str) -> tuple[float, float]:
    cls = DIMENSION_CLASSES.get(dim_name)
    if cls is None:
        return (-float("inf"), float("inf"))
    field = cls.model_fields.get(metric_name)
    if field is None:
        return (-float("inf"), float("inf"))
    lo, hi = -float("inf"), float("inf")
    for meta in field.metadata:
        if hasattr(meta, "ge"):
            lo = meta.ge
        if hasattr(meta, "le"):
            hi = meta.le
    return lo, hi


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def apply_deltas(state: State, deltas: dict[str, float]) -> State:
    """Aplica deltas aditivos ao estado, clampando aos limites de cada métrica.

    Chaves em dot-notation: 'dimensao.metrica' (ex: 'ai_capability.frontier_capability').
    Chaves desconhecidas são ignoradas silenciosamente.
    """
    new_data = state.model_dump()
    for key, delta in deltas.items():
        parts = key.split(".")
        if len(parts) != 2:
            continue
        dim_name, metric_name = parts
        if dim_name not in new_data or metric_name not in new_data[dim_name]:
            continue
        current = new_data[dim_name][metric_name]
        if not isinstance(current, (int, float)):
            continue
        lo, hi = _get_bounds(dim_name, metric_name)
        new_data[dim_name][metric_name] = _clamp(current + delta, lo, hi)
    return State.model_validate(new_data)


# =============================================================================
# Avanço de turno (S1 → S2 → próximo ano S1)
# =============================================================================


def advance_turn(turn: str) -> str:
    year_str, sem_str = turn.split("-")
    year = int(year_str)
    if sem_str == "S1":
        return f"{year}-S2"
    if sem_str == "S2":
        return f"{year + 1}-S1"
    raise ValueError(f"Formato de turno inválido: {turn}")


def list_metric_keys() -> list[str]:
    """Retorna todas as chaves de métrica em dot-notation. Útil pro schema do tool."""
    keys = []
    for dim_name, cls in DIMENSION_CLASSES.items():
        for metric_name in cls.model_fields:
            keys.append(f"{dim_name}.{metric_name}")
    return keys
