"""Cliente Anthropic com tool use forçado para garantir saída estruturada."""
from __future__ import annotations

import os
from typing import Optional

from anthropic import Anthropic
from anthropic.types import ToolUseBlock

from src.config import SimulationConfig
from src.models import (
    ExogenousShock,
    HistoricalEvent,
    State,
    TurnResponse,
    list_metric_keys,
)
from src.prompts import SYSTEM_PROMPT, build_user_message


def _build_tool_schema() -> dict:
    """Schema JSON da tool `advance_turn`. Lista todas as 24 métricas explicitamente."""
    delta_properties = {
        key: {
            "type": "number",
            "description": f"Delta aditivo (positivo ou negativo) aplicado a {key}.",
        }
        for key in list_metric_keys()
    }

    return {
        "name": "advance_turn",
        "description": (
            "Avança a simulação em um semestre. Retorna narrativa, deltas aplicados ao estado "
            "e metadados sobre o evento histórico (se houver)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "narrative": {
                    "type": "string",
                    "description": "Narrativa em português brasileiro, 80-200 palavras.",
                },
                "key_developments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 4,
                    "description": "2 a 4 highlights curtos do semestre.",
                },
                "event_outcome": {
                    "type": "string",
                    "enum": ["ocorreu", "alterado", "anulado", "N/A"],
                    "description": "Como o evento histórico real evoluiu no contrafactual. N/A se não havia evento.",
                },
                "event_outcome_explanation": {
                    "type": ["string", "null"],
                    "description": "Justificativa quando o outcome não foi 'ocorreu' ou 'N/A'.",
                },
                "deltas": {
                    "type": "object",
                    "properties": delta_properties,
                    "additionalProperties": False,
                    "description": (
                        "Deltas aditivos. Inclua apenas métricas que mudaram. "
                        "Métricas omitidas permanecem inalteradas."
                    ),
                },
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Confiança do motor neste turno.",
                },
            },
            "required": [
                "narrative",
                "key_developments",
                "event_outcome",
                "deltas",
                "confidence",
            ],
        },
    }


def get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY não está definida no ambiente. "
            "Copie .env.example para .env e preencha."
        )
    return Anthropic(api_key=api_key)


def simulate_turn(
    client: Anthropic,
    state: State,
    event: Optional[HistoricalEvent],
    shock: Optional[ExogenousShock],
    user_input: Optional[str],
    narrative_history: list[str],
    config: SimulationConfig,
) -> TurnResponse:
    """Executa um turno: chama a API com tool use forçado, retorna TurnResponse validada."""
    user_message = build_user_message(
        state=state,
        event=event,
        shock=shock,
        user_input=user_input,
        narrative_history=narrative_history,
        config=config,
    )

    response = client.messages.create(
        model=config.model,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        system=SYSTEM_PROMPT,
        tools=[_build_tool_schema()],
        tool_choice={"type": "tool", "name": "advance_turn"},
        messages=[{"role": "user", "content": user_message}],
    )

    tool_use_blocks = [b for b in response.content if isinstance(b, ToolUseBlock)]
    if not tool_use_blocks:
        raise RuntimeError(
            f"LLM não retornou tool_use. stop_reason={response.stop_reason}, "
            f"content={response.content}"
        )

    return TurnResponse.model_validate(tool_use_blocks[0].input)
