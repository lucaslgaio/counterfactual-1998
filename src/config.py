"""Configuração de uma run da simulação."""
from __future__ import annotations

import random
from typing import Literal

from pydantic import BaseModel, Field


AIMode = Literal["big_bang", "accelerated_curve"]
PlayMode = Literal["manual", "auto", "hybrid"]


class SimulationConfig(BaseModel):
    """Parâmetros que definem uma run. Salvos junto com o estado pra reprodutibilidade."""

    ai_mode: AIMode = "big_bang"
    play_mode: PlayMode = "manual"

    initial_population_penetration: float = Field(
        default=5.0,
        ge=0.0,
        le=100.0,
        description="% da população usando IA em S1/1998. Sobrescreve o valor base do initial_state.",
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature do LLM. Mais alto = mais variação entre runs.",
    )

    random_shock_probability: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Probabilidade de um choque exógeno por turno.",
    )

    seed: int = Field(
        default_factory=lambda: random.randint(0, 2**31 - 1),
        description="Seed pra reprodutibilidade. Auto-gerada se não fornecida.",
    )

    model: str = Field(
        default="gemini-2.0-flash",
        description="ID do modelo do Google Gemini.",
    )

    max_tokens: int = Field(
        default=2048,
        ge=512,
        description="Max tokens na resposta do LLM.",
    )
