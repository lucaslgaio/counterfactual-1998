"""Side-by-side narrative comparison across two seeds.

Runs the engine + chronicler twice (different seeds, same config) and prints
each turn's narrative side-by-side so you can see how stochastic the chronicle
is at the prose level even when the engine's structure is similar.

Usage:
    export GEMINI_API_KEY="..."
    python scripts/compare_chronicled_runs.py --turns 5 --seeds 42,7
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.chronicler.chronicler import ChroniclerSession
from src.chronicler.gemini_client import GeminiClient
from src.engine.simulation import Simulation, SimulationConfig


def _run_one(seed: int, turns: int, model: str):
    cfg = SimulationConfig(seed=seed)
    sim = Simulation(config=cfg)
    results = sim.run_many(turns)
    states = [results[0].state_before] + [r.state_after for r in results]
    client = GeminiClient.from_env(model=model)
    session = ChroniclerSession(client=client, seed=seed)
    chronicled = [
        session.chronicle_turn(r, states[i], states[i + 1])
        for i, r in enumerate(results)
    ]
    return results, chronicled


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seeds", type=str, default="42,7")
    p.add_argument("--turns", type=int, default=5)
    p.add_argument("--model", type=str, default="gemini-2.5-flash")
    p.add_argument("--width", type=int, default=72)
    args = p.parse_args()

    seeds = [int(s) for s in args.seeds.split(",")]
    if len(seeds) != 2:
        print("ERROR: --seeds must be exactly two comma-separated integers")
        return 1

    print(f"Running {args.turns} turns × 2 seeds ({seeds[0]} vs {seeds[1]})…\n")
    runs = [_run_one(s, args.turns, args.model) for s in seeds]

    width = args.width
    for t in range(args.turns):
        rA, cA = runs[0][0][t], runs[0][1][t]
        rB, cB = runs[1][0][t], runs[1][1][t]
        header = f"=== {rA.turn_label} ==="
        print(header.center(width * 2 + 4))
        print(f"{'-- seed=' + str(seeds[0]):<{width+2}}  {'-- seed=' + str(seeds[1]):<{width+2}}")
        a_lines = textwrap.wrap(cA.narrative, width=width)
        b_lines = textwrap.wrap(cB.narrative, width=width)
        n = max(len(a_lines), len(b_lines))
        for i in range(n):
            la = a_lines[i] if i < len(a_lines) else ""
            lb = b_lines[i] if i < len(b_lines) else ""
            print(f"{la:<{width+2}}  {lb:<{width+2}}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
