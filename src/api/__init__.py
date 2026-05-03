"""HTTP API (FastAPI) que expõe o Modo Jogo ao frontend.

Endpoints:
    POST /game                  → cria nova partida
    GET  /game/{id}/state       → estado atual
    POST /game/{id}/action      → submete ação (canonical ou free)
    GET  /game/{id}/history     → lista de TurnRecords
    GET  /game/missions         → lista missões disponíveis
    GET  /game/canonical_actions → lista ações canônicas

Storage in-memory (dict) — single-process. Não persiste após restart.
"""
