"""Public API: Simulation class. Wraps SpecBundle + WorldState + RNG.

Typical usage:

    sim = Simulation.from_spec()
    results = sim.run_many(58)
    json.dump([r.to_json() for r in results], f)
"""
from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.engine.clamp import MetricRanges, load_metric_ranges
from src.engine.delta_computer import SpecBundle
from src.engine.state import TURN_LABELS, WorldState
from src.engine.turn_runner import (
    DEFAULT_SHOCK_CATALOG,
    SimulationConfig,
    TurnResult,
    run_turn,
)
from src.spec.blocks import load_blocks
from src.spec.dag import load_dag
from src.spec.events import load_events
from src.spec.functions import load_functions

SPEC_DIR_DEFAULT = Path(__file__).parent.parent.parent / "spec"


def build_spec_bundle(spec_dir: Path = SPEC_DIR_DEFAULT) -> SpecBundle:
    """Load all spec files and assemble the SpecBundle the engine consumes."""
    edges = load_dag(spec_dir / "causal_dag.json")
    fns_list = load_functions(spec_dir / "structural_functions.json")
    fns_by_id = {f.edge_id: f for f in fns_list}
    blocks_spec = load_blocks(spec_dir / "geographic_blocks.json")
    events_spec = load_events(spec_dir / "event_variants.json")
    tax = json.loads((spec_dir / "metric_taxonomy.json").read_text(encoding="utf-8"))
    metric_categories: Dict[str, str] = {m["metric_key"]: m["category"] for m in tax["metrics"]}
    metric_ranges: Dict[str, tuple] = {
        m["metric_key"]: tuple(m["range"]) for m in tax["metrics"]
    }
    return SpecBundle(
        edges=edges,
        functions=fns_by_id,
        metric_categories=metric_categories,
        metric_ranges=metric_ranges,
        blocks_spec=blocks_spec,
        events_spec=events_spec,
    )


class Simulation:
    """High-level orchestration of a multi-turn run.

    Holds the current state, the rng, and the history of turn results.
    Designed for use in scripts and from notebooks.
    """

    def __init__(
        self,
        config: Optional[SimulationConfig] = None,
        spec: Optional[SpecBundle] = None,
        spec_dir: Path = SPEC_DIR_DEFAULT,
    ):
        self.config = config or SimulationConfig()
        self.spec = spec or build_spec_bundle(spec_dir)
        self.ranges: MetricRanges = load_metric_ranges(spec_dir)
        self.state: WorldState = WorldState.from_initial_spec(spec_dir)
        self.history: List[TurnResult] = []
        self.rng = np.random.default_rng(self.config.seed)

    # ------------------------------------------------------------------ run

    def run_turn(self, user_input_deltas: Optional[Dict[str, float]] = None) -> TurnResult:
        """Run one turn forward."""
        result = run_turn(
            state=self.state,
            config=self.config,
            spec=self.spec,
            ranges=self.ranges,
            rng=self.rng,
            user_input_deltas=user_input_deltas,
        )
        self.history.append(result)
        self.state = result.state_after
        return result

    def run_many(self, n_turns: int) -> List[TurnResult]:
        """Run ``n_turns`` consecutive turns. Stops at last turn label.

        From the initial state (turn_index=0, label=1998-S1), the maximum
        number of advancement steps is len(TURN_LABELS)-1 = 57: after that
        the state is at turn_index=57, label=2026-S2 and there is nowhere
        further to advance.
        """
        out = []
        remaining = max(0, len(TURN_LABELS) - 1 - self.state.turn_index)
        for _ in range(min(n_turns, remaining)):
            out.append(self.run_turn())
        return out

    # ------------------------------------------------------------------ branching

    def fork_at_turn(self, turn_index: int) -> "Simulation":
        """Return a new Simulation positioned at the state from history[turn_index].

        The fork shares spec/ranges (read-only) but uses a fresh rng derived
        from the parent's seed so that the same forked-from point will diverge
        cleanly. Use ``run_turn(user_input_deltas=...)`` on the fork to branch.
        """
        if turn_index < 0 or turn_index > len(self.history):
            raise IndexError(f"turn_index {turn_index} out of range (0..{len(self.history)})")
        # If turn_index == 0 → fork at initial state; otherwise fork after that turn.
        new_sim = Simulation.__new__(Simulation)
        new_sim.config = copy.deepcopy(self.config)
        new_sim.spec = self.spec
        new_sim.ranges = self.ranges
        if turn_index == 0:
            new_sim.state = WorldState.from_initial_spec()
        else:
            new_sim.state = self.history[turn_index - 1].state_after
        new_sim.history = list(self.history[:turn_index])
        # Derive new rng from a child seed
        new_sim.rng = np.random.default_rng(self.config.seed + turn_index * 1009)
        return new_sim

    # ------------------------------------------------------------------ persistence

    def to_json(self) -> dict:
        return {
            "config": {
                "seed": self.config.seed,
                "shock_overall_probability": self.config.shock_overall_probability,
                "diffusion_alpha": self.config.diffusion_alpha,
            },
            "current_state": self.state.to_json(),
            "history": [r.to_json() for r in self.history],
        }

    @classmethod
    def from_spec(cls, seed: int = 42) -> "Simulation":
        """Convenience: build a fresh Simulation with the given seed."""
        return cls(config=SimulationConfig(seed=seed))
