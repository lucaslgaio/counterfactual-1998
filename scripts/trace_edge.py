"""Show how a specific edge contributed turn-by-turn in a saved run.

Usage:
    python scripts/trace_edge.py --run runs/run_001.json --edge e_001
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=str, required=True, help="Path to a run JSON")
    p.add_argument("--edge", type=str, required=True, help="Edge id, e.g. e_001")
    args = p.parse_args()

    data = json.loads(Path(args.run).read_text(encoding="utf-8"))
    history = data.get("history", [])
    edge_id = args.edge

    print(f"Tracing {edge_id} across {len(history)} turns from {args.run}\n")
    print(f"{'turn':<10} {'source_value':>14} {'contribution':>14} {'form':<20}")
    print("-" * 60)

    n_seen = 0
    for h in history:
        turn_label = h["turn_label"]
        for c in h["delta_package"]["causal_links_active"]:
            if c["edge_id"] == edge_id:
                print(
                    f"{turn_label:<10} {c['source_value']:>14.3f} "
                    f"{c['contribution']:>+14.4f} {c['form']:<20}"
                )
                n_seen += 1

    if n_seen == 0:
        print(
            f"\nEdge {edge_id} did not appear in any turn's top-8 causal_links_active.\n"
            "  (it may still have contributed; only the top contributors are recorded "
            "per turn for performance/UI reasons)"
        )
    else:
        print(f"\n{edge_id} appeared in {n_seen} turn(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
