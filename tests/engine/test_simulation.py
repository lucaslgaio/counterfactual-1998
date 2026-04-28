"""Tests for src/engine/simulation.py — public API."""
from __future__ import annotations

import statistics

from src.engine.simulation import Simulation, SimulationConfig


def test_simulation_runs_58_turns():
    """The full 1998-S1 to 2026-S2 horizon: from initial state we advance
    57 times (58 distinct turn labels, 57 transitions). Calling run_many(58)
    is also valid — it caps at the last turn."""
    sim = Simulation.from_spec(seed=42)
    results = sim.run_many(58)
    # 58 labels = 57 transitions max from initial state
    assert len(results) == 57
    assert sim.state.turn_label == "2026-S2"
    # Each TurnResult corresponds to one of the labels
    assert results[0].turn_label == "1998-S1"
    assert results[-1].turn_label == "2026-S1"
    # state_after of the final result is 2026-S2
    assert results[-1].state_after.turn_label == "2026-S2"


def test_simulation_determinism_cross_run():
    sim_a = Simulation.from_spec(seed=42)
    sim_a.run_many(20)
    sim_b = Simulation.from_spec(seed=42)
    sim_b.run_many(20)
    # Same seed → identical final state
    assert sim_a.state.global_metrics == sim_b.state.global_metrics
    assert sim_a.state.block_metrics == sim_b.state.block_metrics


def test_simulation_variance_across_seeds():
    """Running with different seeds must produce different trajectories on at
    least some metrics (events/shocks introduce variance)."""
    samples = {}
    for seed in [42, 7, 100, 1, 999]:
        sim = Simulation.from_spec(seed=seed)
        sim.run_many(20)
        samples[seed] = sim.state

    # Pick a metric that depends on event/shock outcomes
    vals = [s.global_metrics["financial_markets.global_index"] for s in samples.values()]
    sd = statistics.stdev(vals)
    assert sd > 0, f"financial_markets.global_index has no variance across seeds: {vals}"


def test_simulation_publications_does_not_explode():
    """The CRITICAL invariant from the etapa-4 spec: publications must stay
    below 10x its initial value across 58 turns and 5 different seeds."""
    for seed in [42, 7, 100, 1, 999]:
        sim = Simulation.from_spec(seed=seed)
        sim.run_many(58)
        pubs = sim.state.block_metrics["science_rd.publications_index"]
        max_final = max(pubs.values())
        # Initial US value = 100
        assert max_final < 1000, f"seed={seed}: publications exploded to {max_final}"


def test_simulation_frontier_grows_or_saturates():
    """frontier_capability must NOT decline over the 58 turns; it should grow
    or saturate at its ceiling (100). This is the AI big-bang trajectory."""
    sim = Simulation.from_spec(seed=42)
    sim.run_many(58)
    final = sim.state.block_metrics["ai_capability.frontier_capability"]
    # US started at 92; should be >= 92 after 58 turns
    assert final["US"] >= 92, f"US frontier_capability shrank to {final['US']}"


def test_simulation_to_json_serializable():
    import json

    sim = Simulation.from_spec(seed=42)
    sim.run_many(3)
    js = sim.to_json()
    # Should be JSON-serializable end-to-end
    out = json.dumps(js)
    assert "current_state" in out
    assert "history" in out


def test_simulation_fork_at_turn_diverges_after_input():
    sim = Simulation.from_spec(seed=42)
    sim.run_many(5)
    fork = sim.fork_at_turn(5)
    assert fork.state.turn_index == sim.state.turn_index
    fork.run_turn(user_input_deltas={"financial_markets.global_index": -50.0})
    sim.run_turn()
    # Fork's state should differ from parent's
    assert (
        fork.state.global_metrics["financial_markets.global_index"]
        != sim.state.global_metrics["financial_markets.global_index"]
    )


def test_simulation_run_many_caps_at_final_turn():
    """Calling run_many beyond the last turn label must not crash."""
    sim = Simulation.from_spec(seed=42)
    sim.run_many(58)  # caps at 57
    # Already at last turn — calling more should be a no-op
    extra = sim.run_many(5)
    assert len(extra) == 0
