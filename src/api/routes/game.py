"""Endpoints HTTP do Modo Jogo."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.storage import InMemoryGameStore, get_store
from src.game.canonical_actions import CANONICAL_ACTIONS
from src.game.game_runner import start_game, submit_action
from src.game.gm import GameMaster, GeminiGameMaster
from src.game.missions import MISSIONS_BY_ID, get_mission
from src.game.models import (
    ActionResult,
    CanonicalAction,
    GameState,
    Mission,
    TurnRecord,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/game", tags=["game"])


# Diretório raiz pra logs do GM (runs/game_{id}/gm_log.jsonl)
RUNS_ROOT = Path(__file__).parent.parent.parent.parent / "runs"


# ---------------------------------------------------------------------------- request/response models


class CreateGameRequest(BaseModel):
    seed: int = 42
    mission_id: str = "agi_aligned"


class CreateGameResponse(BaseModel):
    game_id: str
    state: GameState


class SubmitActionRequest(BaseModel):
    type: Literal["canonical", "free"]
    action_id: Optional[str] = None
    prompt: Optional[str] = None


class SubmitActionResponse(BaseModel):
    state: GameState
    action_result: ActionResult


# ---------------------------------------------------------------------------- GM dependency


def get_gm() -> Optional[GameMaster]:
    """Resolve o GM. Retorna None se API key ausente — endpoint só falha se ação
    livre tentar usar. Canonical actions não dependem do GM.

    Override-able em testes via app.dependency_overrides[get_gm].
    """
    try:
        return GeminiGameMaster.from_env()
    except Exception:  # noqa: BLE001 — sem API key etc.
        return None


# ---------------------------------------------------------------------------- endpoints


@router.get("/missions", response_model=List[Mission])
def list_missions():
    return list(MISSIONS_BY_ID.values())


@router.get("/canonical_actions", response_model=List[CanonicalAction])
def list_canonical_actions():
    return CANONICAL_ACTIONS


@router.post("", response_model=CreateGameResponse)
def create_game(
    req: CreateGameRequest,
    store: InMemoryGameStore = Depends(get_store),
):
    try:
        mission = get_mission(req.mission_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    state = start_game(seed=req.seed, mission=mission)
    store.put(state)
    return CreateGameResponse(game_id=state.game_id, state=state)


@router.get("/{game_id}/state", response_model=GameState)
def get_state(
    game_id: str,
    store: InMemoryGameStore = Depends(get_store),
):
    state = store.get(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"partida {game_id!r} não encontrada")
    return state


@router.get("/{game_id}/history", response_model=List[TurnRecord])
def get_history(
    game_id: str,
    store: InMemoryGameStore = Depends(get_store),
):
    state = store.get(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"partida {game_id!r} não encontrada")
    return state.history


@router.post("/{game_id}/action", response_model=SubmitActionResponse)
def submit(
    game_id: str,
    req: SubmitActionRequest,
    store: InMemoryGameStore = Depends(get_store),
    gm: Optional[GameMaster] = Depends(get_gm),
):
    state = store.get(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"partida {game_id!r} não encontrada")

    payload: Dict[str, Any] = {"type": req.type}
    if req.action_id is not None:
        payload["action_id"] = req.action_id
    if req.prompt is not None:
        payload["prompt"] = req.prompt

    if req.type == "free" and gm is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "GM-LLM indisponível (GEMINI_API_KEY/GOOGLE_API_KEY ausente). "
                "Use ações canônicas ou configure a chave no servidor."
            ),
        )

    # Configura log_path do GM real (sem efeito em StubGameMaster)
    if isinstance(gm, GeminiGameMaster):
        gm.log_path = RUNS_ROOT / f"game_{game_id}" / "gm_log.jsonl"

    try:
        new_state, action_result = submit_action(state, payload, gm=gm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("submit_action falhou em %s", game_id)
        raise HTTPException(status_code=500, detail=f"submit_action erro: {exc}")

    store.put(new_state)
    return SubmitActionResponse(state=new_state, action_result=action_result)


@router.delete("/{game_id}")
def delete_game(
    game_id: str,
    store: InMemoryGameStore = Depends(get_store),
):
    deleted = store.delete(game_id)
    return {"deleted": deleted, "game_id": game_id}
