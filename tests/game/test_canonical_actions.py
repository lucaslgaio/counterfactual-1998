"""Testes das ações canônicas — verifica chaves de métrica reais e consistência."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.game.canonical_actions import (
    CANONICAL_ACTIONS,
    CANONICAL_ACTIONS_BY_ID,
    get_canonical_action,
)


def _all_taxonomy_keys() -> set:
    spec = json.loads(
        (Path(__file__).parent.parent.parent / "spec" / "metric_taxonomy.json").read_text()
    )
    out = set()
    BLOCKS = ("US", "EU", "CN", "RoW")
    for m in spec["metrics"]:
        key = m["metric_key"]
        out.add(key)
        if m["category"] == "vectorized":
            for b in BLOCKS:
                out.add(f"{key}.{b}")
        elif m["category"] == "matrix":
            for pair in (m.get("initial_values") or {}).keys():
                out.add(f"{key}.{pair}")
    return out


def test_have_at_least_5_canonical_actions():
    assert len(CANONICAL_ACTIONS) >= 5


def test_all_canonical_actions_have_unique_ids():
    ids = [a.id for a in CANONICAL_ACTIONS]
    assert len(ids) == len(set(ids))


def test_all_canonical_action_metrics_are_real():
    valid = _all_taxonomy_keys()
    for action in CANONICAL_ACTIONS:
        for metric in action.deltas:
            assert metric in valid, (
                f"ação canônica {action.id!r} usa métrica {metric!r} inexistente"
            )


def test_canonical_actions_have_nonempty_prompt_template():
    for action in CANONICAL_ACTIONS:
        assert action.prompt_template.strip(), f"{action.id} sem prompt_template"
        assert len(action.prompt_template.split()) >= 5, (
            f"{action.id} prompt_template muito curto"
        )


def test_get_canonical_action_resolves():
    a = get_canonical_action("push_capability")
    assert a.id == "push_capability"


def test_get_canonical_action_raises_on_unknown():
    with pytest.raises(KeyError):
        get_canonical_action("nope")


def test_canonical_action_costs_use_player_state_fields():
    from src.game.models import PlayerState
    fields = set(PlayerState.model_fields.keys())
    for action in CANONICAL_ACTIONS:
        for cost_field in action.cost:
            assert cost_field in fields, (
                f"ação {action.id} custa campo {cost_field!r} que não existe em PlayerState"
            )
