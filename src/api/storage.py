"""Storage in-memory das partidas. Single-process, sem persistência."""
from __future__ import annotations

import threading
from typing import Dict, Optional

from src.game.models import GameState


class InMemoryGameStore:
    """Dict thread-safe de game_id → GameState.

    FastAPI roda single-worker em dev (uvicorn --reload); em prod multi-worker
    isso quebra (cada worker tem seu store). MVP aceita; v0.2 troca por SQLite.
    """

    def __init__(self):
        self._games: Dict[str, GameState] = {}
        self._lock = threading.Lock()

    def get(self, game_id: str) -> Optional[GameState]:
        with self._lock:
            return self._games.get(game_id)

    def put(self, state: GameState) -> None:
        with self._lock:
            self._games[state.game_id] = state

    def delete(self, game_id: str) -> bool:
        with self._lock:
            return self._games.pop(game_id, None) is not None

    def list_ids(self) -> list:
        with self._lock:
            return list(self._games.keys())


_STORE = InMemoryGameStore()


def get_store() -> InMemoryGameStore:
    """Acessor singleton — pode ser reescrito em testes via dependency_overrides."""
    return _STORE
