"""Tests for src/chronicler/retry.py."""
import pytest

from src.chronicler.retry import (
    MalformedResponseError,
    PermanentError,
    RetryConfig,
    SafetyFilterError,
    TransientError,
    with_retry,
)


def test_with_retry_returns_value_on_first_success():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        return "ok"

    assert with_retry(fn) == "ok"
    assert calls["n"] == 1


def test_with_retry_retries_transient_then_succeeds():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("flaky")
        return "ok"

    cfg = RetryConfig(max_retries=5, initial_backoff_seconds=0.001)
    assert with_retry(fn, config=cfg) == "ok"
    assert calls["n"] == 3


def test_with_retry_eventually_raises_after_max_attempts():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise TransientError("always failing")

    cfg = RetryConfig(max_retries=2, initial_backoff_seconds=0.001)
    with pytest.raises(TransientError):
        with_retry(fn, config=cfg)
    assert calls["n"] == 3  # initial + 2 retries


def test_with_retry_does_not_retry_safety_filter():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise SafetyFilterError("blocked")

    with pytest.raises(SafetyFilterError):
        with_retry(fn, config=RetryConfig(max_retries=3, initial_backoff_seconds=0.001))
    assert calls["n"] == 1


def test_with_retry_does_not_retry_permanent():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise PermanentError("auth failed")

    with pytest.raises(PermanentError):
        with_retry(fn, config=RetryConfig(max_retries=3, initial_backoff_seconds=0.001))
    assert calls["n"] == 1


def test_with_retry_wraps_unknown_exceptions_as_permanent():
    def fn():
        raise ValueError("some unexpected error")

    with pytest.raises(PermanentError, match="some unexpected error"):
        with_retry(fn, config=RetryConfig(max_retries=2, initial_backoff_seconds=0.001))


def test_with_retry_retries_malformed():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 2:
            raise MalformedResponseError("bad function call")
        return "recovered"

    cfg = RetryConfig(max_retries=3, initial_backoff_seconds=0.001)
    assert with_retry(fn, config=cfg) == "recovered"
    assert calls["n"] == 2
