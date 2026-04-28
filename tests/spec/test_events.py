"""Tests for src/spec/events.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.spec.events import (
    DeltaPackage,
    EventVariant,
    EventsSpec,
    HistoricalEventVariants,
    expand_metric_keys,
    load_events,
    validate_events,
)

SPEC_DIR = Path(__file__).parent.parent.parent / "spec"


def test_load_real_events():
    spec = load_events(SPEC_DIR / "event_variants.json")
    assert len(spec.events) == 16, f"expected 16 events, got {len(spec.events)}"


def test_real_events_have_variants_summing_to_one():
    spec = load_events(SPEC_DIR / "event_variants.json")
    for ev in spec.events:
        prob_sum = sum(v.base_probability for v in ev.variants)
        assert 0.99 <= prob_sum <= 1.01, f"{ev.event_id}: variants sum to {prob_sum}"


def test_real_events_validate():
    spec = load_events(SPEC_DIR / "event_variants.json")
    tax_raw = json.loads((SPEC_DIR / "metric_taxonomy.json").read_text(encoding="utf-8"))
    keys = expand_metric_keys(tax_raw["metrics"])
    errors = validate_events(spec, keys)
    assert not errors, f"validation failed: {errors}"


def test_expand_metric_keys_includes_blocks_and_pairs():
    tax_raw = json.loads((SPEC_DIR / "metric_taxonomy.json").read_text(encoding="utf-8"))
    keys = expand_metric_keys(tax_raw["metrics"])
    assert "ai_capability.frontier_capability.US" in keys
    assert "ai_capability.frontier_capability.CN" in keys
    assert "geopolitics.bilateral_tensions.US_CN" in keys
    assert "financial_markets.global_index" in keys


def test_validation_catches_bad_probability_sum():
    spec = EventsSpec(
        events=[HistoricalEventVariants(
            event_id="ev1", turn_label="2020-S1", description="x",
            variants=[
                EventVariant(id="v1", description="x", base_probability=0.3,
                             modulators=[], delta_package_id="pkg1"),
                EventVariant(id="v2", description="x", base_probability=0.3,
                             modulators=[], delta_package_id="pkg1"),
            ],
        )],
        delta_packages={"pkg1": DeltaPackage(id="pkg1", description="x", deltas={})},
        composite_factors={},
    )
    errors = validate_events(spec, set())
    assert any("base_probabilities sum" in e for e in errors)


def test_validation_catches_unknown_delta_package():
    spec = EventsSpec(
        events=[HistoricalEventVariants(
            event_id="ev1", turn_label="2020-S1", description="x",
            variants=[
                EventVariant(id="v1", description="x", base_probability=1.0,
                             modulators=[], delta_package_id="missing_pkg"),
            ],
        )],
        delta_packages={},
        composite_factors={},
    )
    errors = validate_events(spec, set())
    assert any("unknown delta_package_id" in e for e in errors)


def test_validation_catches_unknown_modulator_factor():
    spec = EventsSpec(
        events=[HistoricalEventVariants(
            event_id="ev1", turn_label="2020-S1", description="x",
            variants=[
                EventVariant(id="v1", description="x", base_probability=1.0,
                             modulators=[{"factor": "nonexistent.metric", "coefficient": 0.5}],
                             delta_package_id="pkg1"),
            ],
        )],
        delta_packages={"pkg1": DeltaPackage(id="pkg1", description="x", deltas={})},
        composite_factors={},
    )
    errors = validate_events(spec, {"valid.metric"})
    assert any("unknown modulator factor" in e for e in errors)
