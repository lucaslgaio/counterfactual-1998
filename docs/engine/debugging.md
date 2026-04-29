# Debugging engine trajectories

When a metric does something unexpected, this is the standard path.

## Step 1: get a JSON snapshot

```bash
python scripts/run_simulation.py --seed 42 --turns 58 --output runs/debug.json
```

The resulting file has, for each turn:
- `state_before` and `state_after`
- `delta_package` with both layers (edge / exogenous) split out
- `causal_links_active`: top-8 edges by absolute contribution magnitude
- `sampled_event` and `sampled_shock` with full provenance

## Step 2: scan the trajectory

A quick look at how a metric evolved:

```python
import json
data = json.load(open("runs/debug.json"))
for h in data["history"]:
    val = h["state_after"]["global_metrics"]["financial_markets.systemic_risk"]
    print(f"{h['turn_label']}: systemic_risk = {val:.2f}")
```

If you see a sharp jump, look at that turn's `delta_package`:

```python
turn = data["history"][12]  # whichever turn caused the jump
print(turn["sampled_event"])
print(turn["sampled_shock"])
print(turn["delta_package"]["edge_global_deltas"]["financial_markets.systemic_risk"])
print(turn["delta_package"]["exogenous_global_deltas"].get("financial_markets.systemic_risk"))
```

The two-layer split tells you immediately whether the jump came from edge
dynamics or from an event/shock/user input.

## Step 3: trace a specific edge

```bash
python scripts/trace_edge.py --run runs/debug.json --edge e_010
```

Caveat: only edges that landed in the top-8 contributors per turn are
recorded in `causal_links_active`. Edges with consistently small magnitude
won't show up. To trace them all, you'd need to re-run with a debugger
breakpoint inside `delta_computer.compute_turn_deltas`.

## Step 4: check causal_links_active for a single turn

```python
turn = data["history"][20]
for link in turn["delta_package"]["causal_links_active"]:
    print(f"  {link['edge_id']:8} {link['source']:48} → {link['target']:32} "
          f"src={link['source_value']:.2f} contrib={link['contribution']:+.4f}")
```

This is exactly what the Lovable UI renders in the "why this turn?" panel.

## Common pitfalls

### "Metric is stuck at its ceiling/floor"
Likely the spec's draft alphas are too aggressive for an uncalibrated run.
Check the per-turn growth cap:

```python
# in src/engine/turn_runner.py
MAX_POSITIVE_GROWTH_RATIO = 0.015   # 1.5% per turn
```

That's the safety net before Etapa 5 calibration. If your metric pegs at
the cap every turn, it means the edge contributions exceed the cap — once
calibration lowers alphas the cap should rarely bind.

### "All seeds give identical trajectory"
The deterministic edges dominate the stochastic events/shocks. Pick a
metric that depends more on event outcomes — `financial_markets.global_index`
typically shows variance because crisis events directly add to it.

If even those are identical, check that `Simulation` is being constructed
with the seed you think it is, and that you aren't reusing a fork.

### "Publications exploded"
The `science_rd.publications_index` self-loop (e_131) has explicit
saturation that should keep it bounded. The smoke test
`test_simulation_publications_does_not_explode` runs 5 seeds and
asserts `< 1000` (10× initial). If you see >1000, the saturation
multiplier in `src/engine/functions.py::_apply_saturation` is the place
to look.

### "Frontier_capability is shrinking"
The AI big-bang implies `frontier_capability` should grow or saturate at
100. If it shrinks, the most likely culprits are:
1. An aggregation rule resolved a vector→global edge wrong (check
   `aggregation.py::aggregate`).
2. A negative edge that shouldn't be active (check edge directions and
   contested-direction handling).
3. An event delta_package that subtracts from frontier — check the
   relevant turn's `sampled_event.delta_package_id`.

### "Off-by-one on turn counts"
The state representation is **before** the turn is simulated. Initial
state is `turn_index=0, turn_label=1998-S1`. After simulating one turn,
state advances to `turn_index=1, turn_label=1998-S2`. So
`run_many(58)` from initial state advances 57 times (you can't advance
past `turn_index=57=2026-S2`). 57 TurnResults, 58 distinct labels visited
across all `state_before`/`state_after` snapshots.

## Adding new metrics or edges

The engine reads everything from `spec/*.json`. Adding a new metric
requires:
1. Add it to `spec/metric_taxonomy.json` (with `initial_values` and `range`).
2. Add edges from/to it in `spec/causal_dag.json`.
3. Add a corresponding entry in `spec/structural_functions.json`.
4. Run `python scripts/validate_spec.py` to confirm no broken references.
5. Run `pytest tests/spec/ tests/engine/` — both must still pass.

The engine code itself does NOT need to change for new metrics. If the
engine has trouble with the new metric, that's a routing bug — start in
`delta_computer.py::_resolve_source_value` and `_add_target_delta`.

## Performance

A 58-turn run with seed=42 takes ~50ms on a 2024 MacBook Pro. The
JSON output is ~1.1MB. If you need to run 1000+ simulations for
sensitivity analysis, ~50 seconds total — no need to optimize yet.
Etapa 7 may revisit if/when this becomes a bottleneck.
