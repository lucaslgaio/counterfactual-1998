"""LLM chronicler — narrative interpretation of SDM engine output (Etapa 6).

The chronicler reads a `TurnResult` from `src.engine` and produces prose. It
**never** invents numbers, causal links, or events. The engine decides what
happened; the chronicler writes the history of that.

Public entry point:
    from src.chronicler.chronicler import ChroniclerSession
    from src.chronicler.gemini_client import GeminiClient

    client = GeminiClient.from_env()
    session = ChroniclerSession(client=client, seed=42)
    output = session.chronicle_turn(turn_result, state_before, state_after)
"""
