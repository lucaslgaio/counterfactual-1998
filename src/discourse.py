"""Sementes de debate contemporâneo + rotação de lentes sociológicas.

A cada turno, amostramos 3-4 sementes de debate (datadas com ano de
emergência plausível no contrafactual) e escolhemos uma lente sociológica
de foco. O LLM usa esse material como matéria-prima pra produzir
narrativa concreta em vez de tom genérico.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

DISCOURSE_FILE = Path(__file__).parent.parent / "data" / "discourse_seeds.json"


SOCIOLOGICAL_LENSES = [
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


def turn_to_year(turn: str) -> int:
    return int(turn.split("-")[0])


def load_seeds() -> list[dict[str, Any]]:
    return json.loads(DISCOURSE_FILE.read_text(encoding="utf-8"))


def seeds_for_turn(turn: str, seed: int, max_seeds: int = 4) -> list[dict[str, Any]]:
    """Amostra sementes de debate apropriadas para o turno atual.

    Pondera por recência: sementes datadas dos últimos 3 anos são mais
    prováveis que as de 10+ anos atrás. Determinístico por (seed, turno).
    """
    year = turn_to_year(turn)
    all_seeds = load_seeds()
    eligible = [s for s in all_seeds if s.get("year", 0) <= year]
    if not eligible:
        return []

    weights = []
    for s in eligible:
        age = year - s.get("year", year)
        if age <= 1:
            w = 5
        elif age <= 3:
            w = 3
        elif age <= 7:
            w = 2
        else:
            w = 1
        weights.append(w)

    rng = random.Random(seed + year * 7 + hash(turn))

    picked: list[dict[str, Any]] = []
    pool = list(zip(eligible, weights))
    while len(picked) < max_seeds and pool:
        total = sum(w for _, w in pool)
        r = rng.uniform(0, total)
        acc = 0.0
        for i, (s, w) in enumerate(pool):
            acc += w
            if r <= acc:
                picked.append(s)
                pool.pop(i)
                break
    return picked


def lens_for_turn(turn: str, seed: int) -> str:
    """Escolhe uma lente sociológica de foco pro turno. Determinístico por (seed, turno)."""
    rng = random.Random(seed * 13 + hash(turn))
    return rng.choice(SOCIOLOGICAL_LENSES)
