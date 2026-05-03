"""Fixtures compartilhados pelos testes do módulo game."""
from __future__ import annotations

import pytest

from src.game.gm import StubGameMaster
from src.game.models import GMInterpretation


@pytest.fixture
def stub_gm_default() -> StubGameMaster:
    """GM mock que sempre retorna a interpretação default (research moderado)."""
    return StubGameMaster()


@pytest.fixture
def stub_gm_factory():
    """Factory: cria StubGameMaster com fixed_interpretation arbitrária."""
    def _make(**kwargs) -> StubGameMaster:
        defaults = dict(
            classification="research",
            plausible=True,
            affected_metrics={"ai_capability.frontier_capability.US": 0.5},
            side_effects={},
            cost={"lab_funds": -0.05},
            success_p=0.9,
            triggers_accident=False,
            narrative_seed="O lab faz pesquisa interna.",
        )
        defaults.update(kwargs)
        return StubGameMaster(fixed_interpretation=GMInterpretation(**defaults))
    return _make
