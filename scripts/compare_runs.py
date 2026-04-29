"""Run N simulations with different seeds and report variance per metric.

Usage:
    python scripts/compare_runs.py --n-runs 5 --turns 30 --metrics frontier_capability,gini_intra_block,active_conflicts
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.engine.simulation import Simulation, SimulationConfig


def _resolve_metric(state, metric_short_name):
    """Try to find the metric across global, block (US default), matrix layers."""
    # Try global
    for k, v in state.global_metrics.items():
        if k.endswith(metric_short_name) or metric_short_name in k:
            return ("global", k, v)
    # Try block (return weighted_mean across blocks for short readout)
    for k, sub in state.block_metrics.items():
        if k.endswith(metric_short_name) or metric_short_name in k:
            from src.engine.aggregation import aggregate
            return ("block_wm", k, aggregate(sub, "weighted_mean"))
    # Try matrix
    for k, sub in state.matrix_metrics.items():
        if k.endswith(metric_short_name) or metric_short_name in k:
            return ("matrix_total", k, sub.get("total", 0.0))
    return ("unknown", metric_short_name, float("nan"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n-runs", type=int, default=5)
    p.add_argument("--turns", type=int, default=30)
    p.add_argument(
        "--metrics",
        type=str,
        default="frontier_capability,gini_intra_block,active_conflicts,publications_index,democracy_index",
        help="Comma-separated short metric names",
    )
    p.add_argument("--base-seed", type=int, default=42)
    args = p.parse_args()

    metric_names = [m.strip() for m in args.metrics.split(",") if m.strip()]
    by_metric = {name: [] for name in metric_names}

    for i in range(args.n_runs):
        seed = args.base_seed + i * 17
        sim = Simulation(config=SimulationConfig(seed=seed))
        sim.run_many(args.turns)
        for name in metric_names:
            cat, key, val = _resolve_metric(sim.state, name)
            by_metric[name].append((seed, cat, key, val))

    print(f"=== compare_runs: n={args.n_runs}, turns={args.turns} ===\n")
    print(f"{'metric':<28} {'cat':<10} {'mean':>10} {'sd':>8} {'min':>10} {'max':>10}")
    print("-" * 80)
    for name, rows in by_metric.items():
        if not rows or rows[0][3] != rows[0][3]:  # NaN
            print(f"{name:<28} not found")
            continue
        vals = [r[3] for r in rows]
        cat = rows[0][1]
        key = rows[0][2]
        mean = statistics.mean(vals)
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(
            f"{key[:28]:<28} {cat:<10} {mean:>10.3f} {sd:>8.3f} "
            f"{min(vals):>10.3f} {max(vals):>10.3f}"
        )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
