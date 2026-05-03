"""Testes de missions.py — verifica que as condições usam métricas reais."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.game.missions import MISSION_AGI_ALIGNED, MISSIONS_BY_ID, get_mission


def test_get_mission_returns_known_mission():
    m = get_mission("agi_aligned")
    assert m.id == "agi_aligned"
    assert m is MISSION_AGI_ALIGNED


def test_get_mission_raises_on_unknown():
    with pytest.raises(KeyError):
        get_mission("does_not_exist")


def test_mission_has_at_least_one_win_condition_and_one_lose():
    assert len(MISSION_AGI_ALIGNED.win_conditions) >= 1
    assert len(MISSION_AGI_ALIGNED.lose_conditions) >= 1


def _all_taxonomy_keys() -> set:
    """Carrega todas as chaves válidas do metric_taxonomy + sufixos blocos."""
    spec = json.loads(
        (Path(__file__).parent.parent.parent / "spec" / "metric_taxonomy.json").read_text()
    )
    out = set()
    BLOCKS = ("US", "EU", "CN", "RoW")
    for m in spec["metrics"]:
        key = m["metric_key"]
        cat = m["category"]
        out.add(key)
        if cat == "vectorized":
            for b in BLOCKS:
                out.add(f"{key}.{b}")
        elif cat == "matrix":
            for pair in (m.get("initial_values") or {}).keys():
                out.add(f"{key}.{pair}")
    return out


def test_mission_engine_conditions_use_real_metric_keys():
    """Toda condition com scope=engine deve referir uma chave válida do taxonomy."""
    valid_keys = _all_taxonomy_keys()
    for cond in MISSION_AGI_ALIGNED.win_conditions + MISSION_AGI_ALIGNED.lose_conditions:
        if cond.scope == "engine":
            assert cond.metric in valid_keys, (
                f"missão {MISSION_AGI_ALIGNED.id} usa métrica {cond.metric!r} "
                f"que não existe no metric_taxonomy"
            )


def test_mission_player_conditions_use_real_player_state_fields():
    """Toda condition com scope=player deve usar campo válido de PlayerState."""
    from src.game.models import PlayerState
    valid_fields = set(PlayerState.model_fields.keys())
    for cond in MISSION_AGI_ALIGNED.win_conditions + MISSION_AGI_ALIGNED.lose_conditions:
        if cond.scope == "player":
            assert cond.metric in valid_fields, (
                f"missão usa player metric {cond.metric!r} que não existe em "
                f"PlayerState (campos: {valid_fields})"
            )
