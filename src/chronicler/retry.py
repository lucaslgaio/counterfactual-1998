"""Retry logic for Gemini calls.

Handles transient failures (rate limits, timeouts, malformed function calls)
with bounded exponential backoff. Permanent failures (safety filter blocks,
hard schema mismatches the parser can't recover from) propagate up.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Knobs for retry behavior. Defaults are conservative for paid Gemini API."""

    max_retries: int = 3
    initial_backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    # When the LLM returns malformed function_call output, retry with lower
    # temperature on the second attempt (the determinism helps it recover).
    temperature_after_malformed: float = 0.7


# Categories the runtime maps onto.
class TransientError(Exception):
    """Networking, rate limit, or timeout. Always retry."""


class MalformedResponseError(Exception):
    """LLM returned content that the parser couldn't validate. Retry with lower temp."""


class SafetyFilterError(Exception):
    """LLM blocked the response on safety grounds. Don't retry; surface to caller."""


class PermanentError(Exception):
    """Anything else that's not worth retrying (auth failures, etc.)."""


def with_retry(
    func: Callable[..., Any],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> Any:
    """Call ``func(*args, **kwargs)`` with retry semantics.

    The function is expected to raise one of the four typed exceptions above;
    other exception types are wrapped into ``PermanentError`` and not retried.
    """
    config = config or RetryConfig()
    last_exception: Optional[BaseException] = None

    for attempt in range(config.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except SafetyFilterError as exc:
            logger.warning("safety filter block on attempt %d; not retrying: %s", attempt + 1, exc)
            raise
        except PermanentError:
            raise
        except (TransientError, MalformedResponseError) as exc:
            last_exception = exc
            if attempt == config.max_retries:
                logger.error(
                    "exhausted %d retries; last error: %s",
                    config.max_retries,
                    exc,
                )
                raise
            backoff = config.initial_backoff_seconds * (
                config.backoff_multiplier ** attempt
            )
            logger.warning(
                "attempt %d failed (%s); sleeping %.1fs before retry",
                attempt + 1,
                type(exc).__name__,
                backoff,
            )
            time.sleep(backoff)
        except Exception as exc:  # noqa: BLE001
            # Any other exception is treated as permanent.
            raise PermanentError(str(exc)) from exc

    # Should not reach here.
    if last_exception is not None:
        raise last_exception
    raise PermanentError("retry loop exited without result")
