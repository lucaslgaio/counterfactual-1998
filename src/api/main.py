"""FastAPI app — entry point para `uvicorn src.api.main:app`."""
from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import game

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Counterfactual-1998 — Modo Jogo",
    version="0.1.0",
    description=(
        "API HTTP para o Modo Jogo: jogador é CEO de lab de IA em 1998 e "
        "tenta cumprir a missão escolhida ao longo de 10 turnos semestrais."
    ),
)


# CORS — frontend Vite dev em localhost:5173. Em produção restringir.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
extra = os.environ.get("CORS_ORIGINS")
if extra:
    ALLOWED_ORIGINS.extend(o.strip() for o in extra.split(",") if o.strip())


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(game.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}
