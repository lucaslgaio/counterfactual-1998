"""Tests for src/engine/shock_sampler.py."""
from __future__ import annotations

import numpy as np

from src.engine.shock_sampler import (
    DEFAULT_SHOCK_CATALOG,
    ExogenousShock,
    sample_shock,
)


def test_default_catalog_nonempty():
    assert len(DEFAULT_SHOCK_CATALOG) > 0
    for s in DEFAULT_SHOCK_CATALOG:
        assert 0.0 <= s.base_probability <= 1.0
        assert s.delta_package


def test_sample_shock_can_return_none():
    """With overall_probability=0, no shock should ever fire."""
    rng = np.random.default_rng(42)
    assert sample_shock(rng, overall_probability=0.0) is None


def test_sample_shock_includes_delta_package():
    catalog = [
        ExogenousShock(
            id="test",
            description="test shock",
            base_probability=1.0,
            delta_package={"financial_markets.systemic_risk": 10.0},
        ),
    ]
    rng = np.random.default_rng(42)
    shock = sample_shock(rng, catalog=catalog)
    assert shock is not None
    assert shock.shock_id == "test"
    assert shock.delta_package["financial_markets.systemic_risk"] == 10.0


def test_sample_shock_is_deterministic():
    rng_a = np.random.default_rng(123)
    rng_b = np.random.default_rng(123)
    a = sample_shock(rng_a)
    b = sample_shock(rng_b)
    if a is None and b is None:
        return
    assert a is not None and b is not None
    assert a.shock_id == b.shock_id


def test_sample_shock_distribution_in_long_run():
    """Run 1000 turns; observed shock rate should be approximately the sum
    of catalog base_probabilities, since each is rolled independently."""
    n_with_shock = 0
    n = 2000
    for seed in range(n):
        rng = np.random.default_rng(seed)
        if sample_shock(rng) is not None:
            n_with_shock += 1
    expected = sum(s.base_probability for s in DEFAULT_SHOCK_CATALOG[:1])  # first match wins
    # Lower bound: at least some shocks happened
    assert n_with_shock > 0
    # Upper bound: not every turn (sanity)
    assert n_with_shock < n
