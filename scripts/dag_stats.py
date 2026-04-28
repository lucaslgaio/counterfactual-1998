# DRAFT - revisar com humano
"""Print statistics of the causal DAG.

Usage:
    python scripts/dag_stats.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.spec.dag import build_networkx_graph, load_dag


def main() -> int:
    spec_path = ROOT / "spec" / "causal_dag.json"
    edges = load_dag(spec_path)
    g = build_networkx_graph(edges)

    print("# DAG statistics\n")
    print(f"- **Total edges**: {len(edges)}")
    print(f"- **Nodes (metrics referenced)**: {g.number_of_nodes()}")
    print()

    print("## Magnitude distribution")
    mag = Counter(e.magnitude for e in edges)
    for k in ("strong", "medium", "weak"):
        print(f"- {k}: {mag.get(k, 0)}")
    print()

    print("## Direction distribution")
    direction = Counter(e.direction for e in edges)
    for k in ("positive", "negative"):
        print(f"- {k}: {direction.get(k, 0)}")
    print()

    print("## Scope distribution")
    scope = Counter(e.scope for e in edges)
    for k in ("within_block", "spillover", "global", "matrix_targeted"):
        print(f"- {k}: {scope.get(k, 0)}")
    print()

    print("## Aggregation distribution (vector→global edges)")
    agg = Counter(e.aggregation for e in edges if e.aggregation is not None)
    for k, v in agg.most_common():
        print(f"- {k}: {v}")
    print(f"- (none): {sum(1 for e in edges if e.aggregation is None)}")
    print()

    print("## Direction-contested edges")
    contested = [e for e in edges if e.direction_contested]
    print(f"- count: {len(contested)}")
    for e in contested[:5]:
        print(f"  - {e.id}: {e.source} → {e.target}")
    print()

    print("## Lag distribution (turns)")
    lag = Counter(e.lag_turns for e in edges)
    for k in sorted(lag.keys()):
        print(f"- lag={k}: {lag[k]}")
    print()

    print("## Top 5 hubs (highest out-degree)")
    out_deg = sorted(g.out_degree(), key=lambda kv: -kv[1])
    for node, deg in out_deg[:5]:
        print(f"- `{node}`: {deg} outgoing")
    print()

    print("## Top 5 sinks (highest in-degree)")
    in_deg = sorted(g.in_degree(), key=lambda kv: -kv[1])
    for node, deg in in_deg[:5]:
        print(f"- `{node}`: {deg} incoming")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
