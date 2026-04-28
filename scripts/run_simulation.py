"""Run a single simulation and dump the full history to JSON.

Usage:
    python scripts/run_simulation.py --seed 42 --turns 58 --output run_001.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.engine.simulation import Simulation, SimulationConfig


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=42, help="RNG seed (default: 42)")
    p.add_argument("--turns", type=int, default=58, help="Number of turns (default: 58)")
    p.add_argument(
        "--shock-probability",
        type=float,
        default=1.0,
        help="Multiplier on per-shock base probabilities (default: 1.0)",
    )
    p.add_argument(
        "--output",
        type=str,
        default="run.json",
        help="Output JSON file (default: run.json)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    args = p.parse_args()

    config = SimulationConfig(seed=args.seed, shock_overall_probability=args.shock_probability)
    sim = Simulation(config=config)

    if not args.quiet:
        print(f"Running simulation: seed={args.seed}, turns={args.turns}")

    t0 = time.time()
    results = sim.run_many(args.turns)
    elapsed = time.time() - t0

    if not args.quiet:
        print(f"Completed {len(results)} turns in {elapsed:.2f}s")
        n_events = sum(1 for r in results if r.sampled_event)
        n_shocks = sum(1 for r in results if r.sampled_shock)
        print(f"  events sampled: {n_events}, shocks: {n_shocks}")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    js = sim.to_json()
    out_path.write_text(json.dumps(js, indent=2, ensure_ascii=False))

    if not args.quiet:
        print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
