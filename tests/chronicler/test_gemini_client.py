"""Tests for src/chronicler/gemini_client.py — mocks the genai SDK."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from src.chronicler.gemini_client import (
    GeminiClient,
    build_chronicler_function_declaration,
)
from src.chronicler.retry import (
    MalformedResponseError,
    PermanentError,
    SafetyFilterError,
    TransientError,
)


def test_function_declaration_has_required_fields():
    decl = build_chronicler_function_declaration()
    assert decl["name"] == "chronicle_turn"
    props = decl["parameters"]["properties"]
    assert "narrative" in props
    assert "key_developments" in props
    assert "confidence" in props
    assert "event_outcome_explanation" in props
    assert decl["parameters"]["required"] == ["narrative", "key_developments", "confidence"]


def test_from_env_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(PermanentError, match="API_KEY"):
        GeminiClient.from_env()


def test_from_env_picks_up_gemini_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    client = GeminiClient.from_env()
    assert client.api_key == "fake-key"


def test_from_env_falls_back_to_google_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "fallback-key")
    client = GeminiClient.from_env()
    assert client.api_key == "fallback-key"


def _make_mock_response(narrative: str = "test narrative"):
    """Build a mock genai response with a function_call."""
    fc = MagicMock()
    fc.args = {
        "narrative": narrative,
        "key_developments": ["a", "b", "c"],
        "confidence": "medium",
    }
    part = MagicMock()
    part.function_call = fc
    part.text = None

    content = MagicMock()
    content.parts = [part]

    cand = MagicMock()
    cand.content = content
    cand.finish_reason = "STOP"

    response = MagicMock()
    response.candidates = [cand]
    response.usage_metadata = MagicMock(
        prompt_token_count=100, candidates_token_count=200, total_token_count=300
    )
    return response


def test_call_chronicler_extracts_function_call_args():
    client = GeminiClient(api_key="fake")
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = _make_mock_response()
    client._client = mock_genai_client

    args = client.call_chronicler("system prompt", "user input")
    assert args["narrative"] == "test narrative"
    assert "_metadata" in args
    assert args["_metadata"]["model"] == "gemini-2.5-flash"


def test_call_chronicler_includes_metadata_with_tokens():
    client = GeminiClient(api_key="fake")
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = _make_mock_response()
    client._client = mock_genai_client

    args = client.call_chronicler("system", "user")
    meta = args["_metadata"]
    assert meta["prompt_tokens"] == 100
    assert meta["completion_tokens"] == 200
    assert meta["total_tokens"] == 300
    assert "latency_seconds" in meta


def test_call_chronicler_no_function_call_raises_malformed():
    """Response without function_call.args triggers MalformedResponseError."""
    response = MagicMock()
    response.candidates = []  # no candidates at all
    client = GeminiClient(api_key="fake")
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = response
    client._client = mock_genai_client
    with pytest.raises(MalformedResponseError):
        client.call_chronicler("system", "user")


def test_call_chronicler_translates_rate_limit_to_transient():
    client = GeminiClient(api_key="fake")
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.side_effect = Exception("429 rate limit exceeded")
    client._client = mock_genai_client
    with pytest.raises(TransientError):
        client.call_chronicler("system", "user")


def test_call_chronicler_translates_safety_block_to_safety_filter():
    client = GeminiClient(api_key="fake")
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.side_effect = Exception(
        "Response blocked by safety filter"
    )
    client._client = mock_genai_client
    with pytest.raises(SafetyFilterError):
        client.call_chronicler("system", "user")


def test_call_chronicler_translates_unknown_to_permanent():
    client = GeminiClient(api_key="fake")
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.side_effect = Exception("auth invalid")
    client._client = mock_genai_client
    with pytest.raises(PermanentError):
        client.call_chronicler("system", "user")
