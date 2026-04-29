"""Tests for src/chronicler/discourse.py."""
from collections import Counter

from src.chronicler.discourse import (
    SOCIOLOGICAL_LENSES,
    Seed,
    get_lens_for_turn,
    load_seed_catalog,
    sample_discourse_seeds,
    turn_to_year,
)


def test_turn_to_year():
    assert turn_to_year("1998-S1") == 1998
    assert turn_to_year("2026-S2") == 2026


def test_sociological_lenses_exists():
    assert len(SOCIOLOGICAL_LENSES) >= 10


def test_get_lens_for_turn_deterministic():
    a = get_lens_for_turn(turn_index=5, seed=42)
    b = get_lens_for_turn(turn_index=5, seed=42)
    assert a == b


def test_get_lens_for_turn_varies_across_turns():
    """At least 5 distinct lenses appear across 30 turns with a single seed."""
    lenses_seen = set()
    for t in range(30):
        lenses_seen.add(get_lens_for_turn(turn_index=t, seed=42))
    assert len(lenses_seen) >= 5


def test_load_seed_catalog_real_file():
    seeds = load_seed_catalog()
    assert len(seeds) > 0
    for s in seeds:
        assert isinstance(s, Seed)
        assert s.year >= 1990
        assert s.text


def test_sample_discourse_seeds_deterministic():
    catalog = load_seed_catalog()
    a = sample_discourse_seeds(turn_index=10, turn_label="2003-S2", seed=42, catalog=catalog)
    b = sample_discourse_seeds(turn_index=10, turn_label="2003-S2", seed=42, catalog=catalog)
    assert [s.year for s in a] == [s.year for s in b]
    assert [s.text for s in a] == [s.text for s in b]


def test_sample_discourse_seeds_excludes_future():
    catalog = load_seed_catalog()
    sampled = sample_discourse_seeds(
        turn_index=2, turn_label="1999-S1", seed=42, catalog=catalog, n_seeds=4
    )
    for s in sampled:
        assert s.year <= 1999, f"sampled future seed year={s.year}"


def test_sample_discourse_seeds_returns_n_when_pool_large_enough():
    catalog = load_seed_catalog()
    sampled = sample_discourse_seeds(
        turn_index=40, turn_label="2018-S1", seed=42, catalog=catalog, n_seeds=4
    )
    assert len(sampled) == 4


def test_sample_discourse_seeds_recency_bias():
    """Across many seeds at a late turn, the average sampled year should be
    closer to the current year than the average eligible year — that's the
    recency bias the weighting implements."""
    catalog = load_seed_catalog()
    sampled_years: list = []
    for s in range(80):
        sampled = sample_discourse_seeds(
            turn_index=40, turn_label="2018-S1", seed=s, catalog=catalog, n_seeds=4
        )
        sampled_years.extend(s.year for s in sampled)
    if not sampled_years:
        return
    avg_sampled = sum(sampled_years) / len(sampled_years)
    avg_eligible = sum(s.year for s in catalog if s.year <= 2018) / sum(
        1 for s in catalog if s.year <= 2018
    )
    # Average sampled year should be at least as recent as the average eligible
    # year (the weighting pushes the sampling toward the recent end of the pool).
    assert avg_sampled > avg_eligible, (
        f"avg sampled year {avg_sampled:.1f} not more recent than "
        f"avg eligible year {avg_eligible:.1f}"
    )


def test_seed_to_json_round_trip():
    s = Seed(year=2010, domain="labor", text="some text")
    d = s.to_json()
    s2 = Seed.from_json(d)
    assert s2.year == s.year
    assert s2.domain == s.domain
    assert s2.text == s.text
