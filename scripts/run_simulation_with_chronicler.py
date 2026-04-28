"""Run the engine + chronicle each turn end-to-end.

Combines TurnResult (motor SDM) and ChroniclerOutput (LLM cronista) into a
single JSON output suitable for the Lovable frontend.

Usage:
    export GEMINI_API_KEY="..."
    python scripts/run_simulation_with_chronicler.py \
        --seed 42 --turns 58 --output runs/run_with_narrative.json

Notes:
- Each turn ≈ 5-10s of latency from Gemini Flash.
- 58 turns ≈ 5-10 min of wall time and ~$0.30-0.50 in API cost.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.chronicler.chronicler import ChroniclerSession
from src.chronicler.gemini_client import GeminiClient
from src.engine.simulation import Simulation, SimulationConfig


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--turns", type=int, default=58)
    p.add_argument("--output", type=str, default="runs/run_with_narrative.json")
    p.add_argument("--model", type=str, default="gemini-2.5-flash")
    p.add_argument("--shock-probability", type=float, default=1.0)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if not args.quiet:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Engine first
    config = SimulationConfig(seed=args.seed, shock_overall_probability=args.shock_probability)
    sim = Simulation(config=config)
    if not args.quiet:
        print(f"Running engine: seed={args.seed}, turns={args.turns}…")
    t0 = time.time()
    results = sim.run_many(args.turns)
    engine_elapsed = time.time() - t0
    if not args.quiet:
        n_events = sum(1 for r in results if r.sampled_event)
        n_shocks = sum(1 for r in results if r.sampled_shock)
        print(f"  engine: {len(results)} turns in {engine_elapsed:.2f}s ({n_events} events, {n_shocks} shocks)")

    # Chronicler
    client = GeminiClient.from_env(model=args.model)
    session = ChroniclerSession(client=client, seed=args.seed)
    states = [results[0].state_before] + [r.state_after for r in results]
    chronicled = []
    if not args.quiet:
        print(f"Chronicling {len(results)} turns via {args.model}…")
    t0 = time.time()
    for i, r in enumerate(results):
        out = session.chronicle_turn(r, states[i], states[i + 1])
        chronicled.append(out)
        if not args.quiet and (i + 1) % 5 == 0:
            print(f"  chronicled {i + 1}/{len(results)} turns")
    chronicler_elapsed = time.time() - t0
    if not args.quiet:
        print(f"  chronicler: {len(chronicled)} turns in {chronicler_elapsed:.2f}s")

    # Combined output
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    combined = {
        "config": {
            "seed": args.seed,
            "turns": args.turns,
            "model": args.model,
            "shock_overall_probability": args.shock_probability,
        },
        "engine_runtime_seconds": engine_elapsed,
        "chronicler_runtime_seconds": chronicler_elapsed,
        "current_state": sim.state.to_json(),
        "turns": [
            {
                "turn_result": r.to_json(),
                "chronicler_output": c.to_json(),
            }
            for r, c in zip(results, chronicled)
        ],
    }
    out_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.quiet:
        print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
