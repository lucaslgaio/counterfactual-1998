"""Testes da API HTTP — usa TestClient + GM mockado via dependency_overrides."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routes.game import get_gm
from src.api.storage import InMemoryGameStore, get_store
from src.game.gm import StubGameMaster
from src.game.models import GMInterpretation


@pytest.fixture
def client():
    """Reset do store + GM stub injetado por todos os endpoints."""
    fresh_store = InMemoryGameStore()

    def _store_override():
        return fresh_store

    def _gm_override():
        return StubGameMaster(
            fixed_interpretation=GMInterpretation(
                classification="research",
                plausible=True,
                affected_metrics={"ai_capability.frontier_capability.US": 0.5},
                side_effects={},
                cost={"lab_funds": -0.05},
                success_p=1.0,  # determinístico
                triggers_accident=False,
                narrative_seed="O lab faz pesquisa interna.",
            )
        )

    app.dependency_overrides[get_store] = _store_override
    app.dependency_overrides[get_gm] = _gm_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --------------------------- meta endpoints


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_missions(client):
    r = client.get("/game/missions")
    assert r.status_code == 200
    missions = r.json()
    assert any(m["id"] == "agi_aligned" for m in missions)


def test_list_canonical_actions(client):
    r = client.get("/game/canonical_actions")
    assert r.status_code == 200
    actions = r.json()
    assert len(actions) >= 5
    ids = [a["id"] for a in actions]
    assert "push_capability" in ids


# --------------------------- create + state


def test_create_game_returns_state(client):
    r = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"})
    assert r.status_code == 200
    body = r.json()
    assert body["game_id"]
    assert body["state"]["current_turn"] == 0
    assert body["state"]["status"] == "in_progress"
    assert body["state"]["mission"]["id"] == "agi_aligned"


def test_create_game_unknown_mission_returns_400(client):
    r = client.post("/game", json={"seed": 42, "mission_id": "nope"})
    assert r.status_code == 400


def test_get_state_404_for_unknown(client):
    r = client.get("/game/zzz/state")
    assert r.status_code == 404


def test_get_state_after_create(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    r = client.get(f"/game/{gid}/state")
    assert r.status_code == 200
    assert r.json()["game_id"] == gid


# --------------------------- actions


def test_submit_canonical_action(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    r = client.post(f"/game/{gid}/action", json={"type": "canonical", "action_id": "push_capability"})
    assert r.status_code == 200
    body = r.json()
    assert body["state"]["current_turn"] == 1
    assert body["action_result"]["action_type"] == "canonical"
    assert body["action_result"]["outcome"] == "success"


def test_submit_free_action_uses_overridden_gm(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    r = client.post(
        f"/game/{gid}/action",
        json={"type": "free", "prompt": "Recrutamos PhDs"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["action_result"]["action_type"] == "free"
    assert body["state"]["current_turn"] == 1


def test_submit_action_invalid_payload_400(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    # type=canonical sem action_id
    r = client.post(f"/game/{gid}/action", json={"type": "canonical"})
    assert r.status_code == 400


def test_submit_action_unknown_canonical_404(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    r = client.post(
        f"/game/{gid}/action",
        json={"type": "canonical", "action_id": "made_up_action"},
    )
    assert r.status_code == 404


def test_submit_action_unknown_game_404(client):
    r = client.post(
        "/game/nonexistent/action",
        json={"type": "canonical", "action_id": "push_capability"},
    )
    assert r.status_code == 404


# --------------------------- history


def test_history_empty_after_create(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    r = client.get(f"/game/{gid}/history")
    assert r.status_code == 200
    assert r.json() == []


def test_history_grows_with_actions(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    for _ in range(3):
        client.post(
            f"/game/{gid}/action",
            json={"type": "canonical", "action_id": "push_capability"},
        )
    r = client.get(f"/game/{gid}/history")
    assert r.status_code == 200
    history = r.json()
    assert len(history) == 3


# --------------------------- delete


def test_delete_game(client):
    create = client.post("/game", json={"seed": 42, "mission_id": "agi_aligned"}).json()
    gid = create["game_id"]
    r = client.delete(f"/game/{gid}")
    assert r.status_code == 200
    assert r.json()["deleted"] is True
    # Subsequente get → 404
    r2 = client.get(f"/game/{gid}/state")
    assert r2.status_code == 404
