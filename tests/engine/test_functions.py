"""Tests for src/engine/functions.py."""
from __future__ import annotations

import math

import pytest

from src.engine.functions import (
    DEFAULT_MAGNITUDE_ALPHA,
    FunctionContext,
    evaluate,
    exponential_decay,
    linear,
    log_linear,
    sigmoid,
    sigmoid_temporal,
)


# ---------------------------------------------------------------------------- linear


def test_linear_alpha_zero_gives_zero():
    ctx = FunctionContext()
    assert linear(50.0, {"alpha": 0.0}, ctx) == 0.0


def test_linear_basic():
    ctx = FunctionContext()
    # alpha=0.04, source=92 → delta = 3.68 (e_001 example)
    assert abs(linear(92.0, {"alpha": 0.04}, ctx) - 3.68) < 1e-9


def test_linear_negative_alpha():
    ctx = FunctionContext()
    assert linear(60.0, {"alpha": -0.02}, ctx) == -1.2


# ---------------------------------------------------------------------------- log_linear


def test_log_linear_zero_source():
    ctx = FunctionContext()
    assert log_linear(0.0, {"alpha": 0.5, "beta": 10.0}, ctx) == 0.0


def test_log_linear_diminishing_returns():
    ctx = FunctionContext()
    d_low = log_linear(10.0, {"alpha": 1.0, "beta": 5.0}, ctx)
    d_high = log_linear(100.0, {"alpha": 1.0, "beta": 5.0}, ctx)
    # Doubling source 10x doesn't 10x the delta
    assert d_high < 10 * d_low


def test_log_linear_handles_negative_beta():
    ctx = FunctionContext()
    # negative beta should fall back to 1.0 without crashing
    d = log_linear(10.0, {"alpha": 1.0, "beta": -5.0}, ctx)
    assert d > 0


# ---------------------------------------------------------------------------- sigmoid


def test_sigmoid_at_saturation_returns_zero():
    """When target is at its max, headroom=0 → delta=0 regardless of source."""
    ctx = FunctionContext(target_range=(0, 100))
    d = sigmoid(
        source_value=80.0,
        params={"alpha": 0.05, "midpoint": 50.0, "_target_current": 100.0},
        ctx=ctx,
    )
    assert d == 0.0


def test_sigmoid_below_midpoint_small_delta():
    ctx = FunctionContext(target_range=(0, 100))
    d_below = sigmoid(
        source_value=10.0,
        params={"alpha": 0.05, "midpoint": 50.0, "_target_current": 50.0},
        ctx=ctx,
    )
    d_above = sigmoid(
        source_value=90.0,
        params={"alpha": 0.05, "midpoint": 50.0, "_target_current": 50.0},
        ctx=ctx,
    )
    assert d_above > d_below


# ---------------------------------------------------------------------------- exponential_decay


def test_exponential_decay_fades_over_time():
    p = {"alpha": 0.5, "beta": 4.0}
    d_now = exponential_decay(100.0, p, FunctionContext(elapsed_turns=0))
    d_later = exponential_decay(100.0, p, FunctionContext(elapsed_turns=20))
    assert d_later < 0.1 * d_now


def test_exponential_decay_at_t0():
    d = exponential_decay(100.0, {"alpha": 0.5, "beta": 4.0}, FunctionContext(elapsed_turns=0))
    assert abs(d - 50.0) < 1e-6  # exp(0)=1 → 0.5*100*1


# ---------------------------------------------------------------------------- sigmoid_temporal


def test_sigmoid_temporal_pre_threshold():
    p = {"alpha_pre": 0.01, "alpha_post": 0.05, "threshold": 30.0}
    ctx = FunctionContext(activation_value=10.0)
    d = sigmoid_temporal(50.0, p, ctx)
    # alpha_pre=0.01, source=50 → 0.5
    assert abs(d - 0.5) < 1e-9


def test_sigmoid_temporal_post_threshold():
    p = {"alpha_pre": 0.01, "alpha_post": 0.05, "threshold": 30.0}
    ctx = FunctionContext(activation_value=40.0)
    d = sigmoid_temporal(50.0, p, ctx)
    # alpha_post=0.05, source=50 → 2.5
    assert abs(d - 2.5) < 1e-9


# ---------------------------------------------------------------------------- evaluate dispatch


def test_evaluate_unknown_form_raises():
    with pytest.raises(ValueError, match="unknown structural form"):
        evaluate("nope", 10.0, 5.0, {})


def test_evaluate_dispatches_correctly():
    d = evaluate("linear", 50.0, 0.0, {"alpha": 0.1})
    assert d == 5.0


# ---------------------------------------------------------------------------- saturation invariant (e_131)


def test_self_loop_saturation_prevents_explosion():
    """The critical invariant: a self-loop with sustained positive delta must
    converge, not explode. Simulates 100 iterations of e_131-like behavior."""
    ctx = FunctionContext(target_range=(0, 10000), is_self_loop=True)
    target = 100.0  # publications_index initial value
    for _ in range(100):
        # Every turn, evaluate publications self-loop
        delta = evaluate("linear", target, target, {"alpha": 0.04}, ctx)
        target += delta
    # Without saturation, target would explode (geometric growth).
    # With saturation, it should approach the upper bound but stay below.
    assert target < 10000, f"target exploded to {target}"
    assert target > 100, f"target stagnated at {target}"


def test_self_loop_without_range_has_soft_cap():
    """If target_range isn't provided, growth is capped at 5%/turn."""
    ctx = FunctionContext(is_self_loop=True)  # no target_range
    target = 100.0
    delta = evaluate("linear", target, target, {"alpha": 1.0}, ctx)
    # Without saturation, delta = 1.0 * 100 = 100 (100% growth!).
    # With soft cap, capped at 5% of target = 5.
    assert delta <= 5.0


def test_negative_delta_not_saturated():
    """Self-loops with negative delta (decay) shouldn't be muted by saturation."""
    ctx = FunctionContext(target_range=(0, 100), is_self_loop=True)
    delta = evaluate("linear", 50.0, 90.0, {"alpha": -0.1}, ctx)
    assert delta < 0  # decay flows through


# ---------------------------------------------------------------------------- defaults


def test_default_magnitude_alpha_table():
    assert DEFAULT_MAGNITUDE_ALPHA["weak"] == 0.1
    assert DEFAULT_MAGNITUDE_ALPHA["medium"] == 0.3
    assert DEFAULT_MAGNITUDE_ALPHA["strong"] == 0.7
    assert DEFAULT_MAGNITUDE_ALPHA["negligible"] == 0.02
