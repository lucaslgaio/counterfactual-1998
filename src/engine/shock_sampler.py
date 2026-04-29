"""Sample exogenous shocks (stochastic deltas not anchored to historical events).

Shocks are pulled from a small catalog (financial scare, geopolitical
incident, technological breakthrough, pandemic-like). Each shock has a
delta_package and a base probability; per-turn the engine rolls each shock
independently.

Determinism: rng is split per-turn upstream so the same seed gives the
same shock sequence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class ExogenousShock:
    """A single shock blueprint."""

    id: str
    description: str
    base_probability: float  # per-turn
    delta_package: Dict[str, float]  # {metric_key: delta}


@dataclass
class SampledShock:
    """A shock that fired this turn."""

    shock_id: str
    description: str
    delta_package: Dict[str, float]
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "shock_id": self.shock_id,
            "description": self.description,
            "delta_package": dict(self.delta_package),
            "provenance": dict(self.provenance),
        }


# Default catalog. Calibration in Etapa 5 may revise probabilities and deltas.
DEFAULT_SHOCK_CATALOG: List[ExogenousShock] = [
    ExogenousShock(
        id="financial_scare",
        description="Market scare unrelated to historical events (small risk-off episode).",
        base_probability=0.04,
        delta_package={
            "financial_markets.systemic_risk": 5.0,
            "financial_markets.global_index": -3.0,
        },
    ),
    ExogenousShock(
        id="geopolitical_incident",
        description="Brief geopolitical flare-up between two blocks.",
        base_probability=0.05,
        delta_package={
            "geopolitics.bilateral_tensions.US_CN": 3.0,
            "financial_markets.systemic_risk": 1.5,
        },
    ),
    ExogenousShock(
        id="tech_breakthrough",
        description="Unanticipated R&D breakthrough in a frontier lab.",
        base_probability=0.06,
        delta_package={
            "science_rd.breakthroughs_per_year.US": 1.5,
            "ai_capability.frontier_capability.US": 0.5,
        },
    ),
    ExogenousShock(
        id="pandemic_warning",
        description="Localized outbreak that doesn't reach historical-pandemic scale.",
        base_probability=0.02,
        delta_package={
            "health.life_expectancy": -0.05,
            "financial_markets.systemic_risk": 1.0,
        },
    ),
]


def sample_shock(
    rng: np.random.Generator,
    catalog: Optional[List[ExogenousShock]] = None,
    overall_probability: float = 1.0,
) -> Optional[SampledShock]:
    """Roll for a shock this turn.

    Each shock in ``catalog`` is checked independently with probability
    ``shock.base_probability * overall_probability``. If multiple fire, the
    first one wins (rare for sane probabilities). Returns None if nothing
    fires.
    """
    catalog = catalog if catalog is not None else DEFAULT_SHOCK_CATALOG
    for shock in catalog:
        p = float(shock.base_probability) * float(overall_probability)
        if rng.random() < p:
            return SampledShock(
                shock_id=shock.id,
                description=shock.description,
                delta_package=dict(shock.delta_package),
                provenance={"base_probability": shock.base_probability},
            )
    return None
