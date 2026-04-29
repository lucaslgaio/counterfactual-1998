# Engine — Deterministic System Dynamics simulator (Etapa 4)

## What it is

A pure-Python motor that consumes the formal DAG specification (`spec/*.json`)
and produces, turn by turn, a structured trajectory of the counterfactual
1998–2026 world. **No LLM is called anywhere in this module** — that is the
job of the cronista layer (Etapa 6).

The engine is the bridge between the spec (declarative) and the chronicle
(narrative). Anything you feed into it is fully deterministic given a seed:
two runs with the same `(seed, config, spec)` produce byte-identical states.

## What's in the box

```
src/engine/
├── state.py            # WorldState (frozen dataclass) + initial-state loader
├── functions.py        # 5 structural forms (linear, log_linear, sigmoid, exponential_decay, sigmoid_temporal)
├── aggregation.py      # vector→global aggregation (leader / weighted_mean / max / sum)
├── clamp.py            # range enforcement (per metric, post-deltas)
├── spillover.py        # Bass-style cross-block diffusion
├── event_sampler.py    # historical-anchored variant lottery (with composite-factor modulators)
├── shock_sampler.py    # exogenous random shocks
├── delta_computer.py   # the heart: evaluate the DAG for one turn
├── turn_runner.py      # orchestrate sample → compute deltas → apply → clamp
└── simulation.py       # public Simulation class with run_turn / run_many / fork / to_json
```

Companion scripts:
```
scripts/
├── run_simulation.py   # CLI: run N turns, dump JSON
├── compare_runs.py     # CLI: variance across seeds
└── trace_edge.py       # CLI: how did edge X contribute over time?
```

Companion tests live under `tests/engine/` and run with `pytest tests/engine/`.

## How a turn flows

```
state_t  ──┐
           ▼
    sample_event(turn_label)   sample_shock(rng)         user_input_deltas
           │                          │                         │
           └────────┬─────────────────┴─────────────────────────┘
                    ▼
            compute_turn_deltas
                    │
   ┌────────────────┼────────────────────┐
   ▼                ▼                    ▼
edges (DAG)     spillover         exogenous (event/shock/user)
   │                │                    │
   └────────┬───────┴────────────────────┘
            ▼
      DeltaPackage  (edge_layer, exogenous_layer separately)
            │
            ▼
     apply edges-with-cap + exogenous-uncapped → new state
            │
            ▼
        clamp ranges
            │
            ▼
        state_{t+1}
```

The two-layer DeltaPackage matters: pre-Etapa-5 calibration, the spec's
draft alphas can drive metrics into saturation in 58 turns. We cap
**edge-derived** positive growth at 1.5%/turn so the DAG dynamics don't
flatten the simulation into a single attractor — but **exogenous deltas**
(events/shocks/user inputs) flow through uncapped because they're
discrete, intentional, hand-authored values. This split is a temporary
safety net: Etapa 5 will calibrate alphas against historical data and the
cap will rarely (or never) bind.

## Running a simulation

```python
from src.engine.simulation import Simulation

sim = Simulation.from_spec(seed=42)
results = sim.run_many(58)        # 57 advancement steps from 1998-S1 → 2026-S2

# Inspect anything
print(sim.state.global_metrics["financial_markets.global_index"])
print(results[0].sampled_event)   # variant for 1998-S1 if anchored, else None
print(results[10].delta_package.causal_links_active)  # top contributors that turn
```

From the CLI:
```bash
python scripts/run_simulation.py --seed 42 --turns 58 --output runs/run_001.json
python scripts/compare_runs.py --n-runs 5 --turns 30
python scripts/trace_edge.py --run runs/run_001.json --edge e_001
```

## Design principles

1. **Deterministic given seed**. Every random draw goes through a
   `numpy.random.Generator` derived from `SimulationConfig.seed`. No global
   `random`, no `time`-based seeding.

2. **Immutable state**. `WorldState` is a frozen dataclass; advancing one
   turn returns a new object. No in-place mutation across `run_turn` boundaries.

3. **Provenance everywhere**. `DeltaPackage` records, per turn, which
   edges fired with what `source_value` and `contribution`. The Lovable UI
   reads `causal_links_active` directly.

4. **Two-layer deltas**. `edge_*_deltas` (capped) and `exogenous_*_deltas`
   (uncapped) are tracked separately so the cap doesn't muffle event
   visibility. Both are merged on read for callers that don't care.

5. **No LLM**. Reaffirming. The engine does not import any LLM SDK. The
   spec author and the chronicle author both work *around* the engine, not
   *through* it.

## Smoke-test invariants

Every `pytest tests/engine/` run verifies:

- 58 turns complete without errors.
- Same seed → identical final state.
- Different seeds → measurable variance on at least one global metric.
- `science_rd.publications_index` stays below 10× initial value (the e_131
  self-loop saturation guarantee).
- `ai_capability.frontier_capability` does not shrink (US starts at 92,
  must end ≥ 92 after the AI big-bang trajectory).
- All metrics stay within their declared ranges in `metric_taxonomy.json`.

## Where to look when something is off

See `docs/engine/debugging.md` for the standard debugging walkthrough.

## Etapa 4 vs Etapa 5

This module is **uncalibrated**. The alphas in `spec/structural_functions.json`
are draft. The growth cap in `turn_runner.py::MAX_POSITIVE_GROWTH_RATIO` is a
safety net that prevents pathological saturation but also flattens the
trajectory more than a calibrated model would. Etapa 5 calibrates alphas
against historical data (1998–2024) and may remove the cap entirely.

This module is **untouched by LLM**. The engine produces structured JSON;
the LLM cronista (Etapa 6) reads that JSON and writes prose. The two
layers never share a function call.
