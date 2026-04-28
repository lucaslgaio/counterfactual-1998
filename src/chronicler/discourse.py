"""Sociological lens rotation + discourse seed sampling for the chronicler.

Adapted from src/discourse.py — reused logic, but with explicit (turn_index,
seed) determinism so the chronicler reproduces identical lens/seeds across
runs given the same RNG seed. The chronicler is purely interpretive; this
module decides what *angle* the interpretation comes from.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

DISCOURSE_FILE = Path(__file__).parent.parent.parent / "data" / "discourse_seeds.json"


# 10 sociological lenses. Each turn rotates through them via (seed, turn_index).
SOCIOLOGICAL_LENSES: List[str] = [
    "trabalho e classe — quem ganha/perde, sindicalização, novas e velhas profissões em colapso, demissões",
    "vida íntima — relacionamentos com IA, parentalidade, amizade, sexualidade, solidão epidêmica",
    "conhecimento e educação — escolas, universidades, atrofia cognitiva, novos saberes, geração-IA",
    "política e identidade — ideologias novas, movimentos sociais, polarização, autoritarismo, partidos",
    "religião e sentido — AGI como divindade, niilismo, neo-monasticismo, longtermismo, racionalismo",
    "cultura e arte — o que se cria e consome, gírias novas, ritualidade, memes, formas estéticas",
    "resistência e contraculturas — neo-luditismo, retorno ao analógico, zonas livres de IA, sabotagem",
    "geografia — cidades epicentros, êxodo de cérebros, infraestrutura crítica, divisões regionais",
    "corpo e saúde — medicina, dependência cognitiva, ansiedade, suicídio, novos diagnósticos",
    "cidadania e direito — novos direitos, novos crimes, soberania, vigilância, processos judiciais",
]


@dataclass
class Seed:
    """A single discourse seed: contemporary debate snippet anchored to a year/domain."""

    year: int
    domain: str
    text: str

    def to_json(self) -> dict:
        return {"year": self.year, "domain": self.domain, "text": self.text}

    @classmethod
    def from_json(cls, data: dict) -> "Seed":
        return cls(
            year=int(data.get("year", 0)),
            domain=str(data.get("domain", "")),
            text=str(data.get("text", "")),
        )


def turn_to_year(turn_label: str) -> int:
    """'1998-S1' → 1998."""
    return int(turn_label.split("-")[0])


def load_seed_catalog(path: Path = DISCOURSE_FILE) -> List[Seed]:
    """Load all discourse seeds from the project's JSON catalog."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Seed.from_json(s) for s in raw]


# ---------------------------------------------------------------------------- public API


def get_lens_for_turn(turn_index: int, seed: int) -> str:
    """Determinístico: dado (turn_index, seed), sempre a mesma lente.

    Uses ``(seed * 13 + turn_index)`` as the rng input so consecutive turns
    cycle through different lenses (rather than locking onto one).
    """
    rng = random.Random(seed * 13 + turn_index)
    return rng.choice(SOCIOLOGICAL_LENSES)


def sample_discourse_seeds(
    turn_index: int,
    turn_label: str,
    seed: int,
    catalog: List[Seed],
    n_seeds: int = 4,
) -> List[Seed]:
    """Pick ``n_seeds`` discourse seeds, weighted by recency.

    Recency weighting (relative to the year of ``turn_label``):
        - ≤1 year old: weight 5
        - ≤3 years: weight 3
        - ≤7 years: weight 2
        - older: weight 1
        - future seeds (year > current): excluded

    Determinístico por (seed, turn_index, turn_label).
    """
    year = turn_to_year(turn_label)
    eligible = [s for s in catalog if s.year <= year]
    if not eligible:
        return []

    weights = []
    for s in eligible:
        age = year - s.year
        if age <= 1:
            weights.append(5)
        elif age <= 3:
            weights.append(3)
        elif age <= 7:
            weights.append(2)
        else:
            weights.append(1)

    rng = random.Random(seed + year * 7 + turn_index * 17 + hash(turn_label))

    picked: List[Seed] = []
    pool = list(zip(eligible, weights))
    while len(picked) < n_seeds and pool:
        total = sum(w for _, w in pool)
        if total == 0:
            break
        r = rng.uniform(0, total)
        acc = 0.0
        for i, (s, w) in enumerate(pool):
            acc += w
            if r <= acc:
                picked.append(s)
                pool.pop(i)
                break
    return picked
