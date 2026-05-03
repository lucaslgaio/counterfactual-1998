"""Teste de integração do GM real (Gemini). Pulado se GEMINI_API_KEY ausente.

Valida apenas que:
1. A chamada vai e volta sem exceção.
2. O retorno respeita o schema (GMInterpretation).
3. As métricas afetadas são chaves válidas do taxonomy.
4. Magnitudes saem dentro dos caps (após clip).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.game.config import CATEGORY_CAPS, list_available_metrics
from src.game.gm import GeminiGameMaster, clip_interpretation


pytestmark = pytest.mark.skipif(
    not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
    reason="requires GEMINI_API_KEY/GOOGLE_API_KEY env var",
)


def test_gm_interprets_simple_action(tmp_path):
    log = tmp_path / "gm_log.jsonl"
    gm = GeminiGameMaster.from_env(log_path=log)

    interp = gm.interpret(
        prompt="Recrutamos 10 PhDs em alignment para um time interno de segurança.",
        year=1999.0,
        turn=2,
        mission_name="AGI Alinhada",
        mission_description="Construir IA segura.",
        engine_state_summary=(
            "frontier_capability.US=92, EU=78, CN=35\n"
            "media_trust=53, democracy_index.US=8.0"
        ),
        player_state={"lab_funds": 1.0, "accidents_count": 0, "reputation": 0.5},
        recent_history=["push_capability"],
    )
    assert interp.classification in {
        "research", "deployment", "lobby", "partnership", "comms", "m_and_a", "rejected",
    }
    assert isinstance(interp.plausible, bool)
    assert 0.0 <= interp.success_p <= 1.0
    assert interp.narrative_seed
    assert log.exists()

    # Magnitudes (após clip) dentro dos caps
    clipped, _ = clip_interpretation(interp)
    if clipped.plausible:
        cap = CATEGORY_CAPS[clipped.classification]["max_metric_delta"]
        for v in clipped.affected_metrics.values():
            assert abs(v) <= cap + 1e-9
        for v in clipped.side_effects.values():
            assert abs(v) <= cap + 1e-9


def test_gm_uses_only_real_metrics(tmp_path):
    """Métricas que o GM retornar devem estar no taxonomy (após coação Pydantic)."""
    valid = set(list_available_metrics())
    gm = GeminiGameMaster.from_env(log_path=tmp_path / "log.jsonl")

    interp = gm.interpret(
        prompt="Lançamos um produto comercial em massa.",
        year=2002.0, turn=8,
        mission_name="AGI Alinhada", mission_description="x",
        engine_state_summary="ai_capability.frontier_capability.US=94",
        player_state={"lab_funds": 0.7, "accidents_count": 0, "reputation": 0.5},
        recent_history=[],
    )
    # Algumas métricas podem ter sido inventadas; aceita warning, não falha hard
    invented = [k for k in (interp.affected_metrics | interp.side_effects)
                if k not in valid]
    if invented:
        pytest.fail(
            f"GM inventou métricas que não estão no taxonomy: {invented}"
        )
