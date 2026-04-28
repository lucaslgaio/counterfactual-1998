# DRAFT - revisar com humano
"""Render the causal DAG to SVG and PNG using Graphviz.

Nodes colored by cluster. Edges colored by scope, line styles by lag.
Edge thickness proportional to magnitude.

Usage:
    python scripts/render_dag.py

Outputs:
    docs/causal_dag/diagram.svg
    docs/causal_dag/diagram.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import graphviz

from src.spec.dag import _strip_block_suffix, load_dag


CLUSTER_COLORS = {
    "tecnologia_ia": "#22d3ee",
    "economia": "#a78bfa",
    "sociedade": "#fbbf24",
    "conhecimento_saude": "#34d399",
    "politica": "#f87171",
    "informacao_ambiente": "#94a3b8",
}

SCOPE_EDGE_COLOR = {
    "within_block": "#1e40af",
    "spillover": "#ca8a04",
    "global": "#475569",
}

MAGNITUDE_THICKNESS = {
    "weak": "0.6",
    "medium": "1.4",
    "strong": "2.8",
}


def _short_label(metric_key: str) -> str:
    """Short display label for a node."""
    parts = metric_key.split(".")
    if len(parts) >= 2:
        return parts[-1].replace("_", " ")
    return metric_key


def _cluster_for(metric_key: str, taxonomy: dict) -> str:
    base_key = _strip_block_suffix(metric_key)
    return taxonomy.get(base_key, {}).get("cluster", "outro")


def main() -> int:
    spec_dir = ROOT / "spec"
    dag_path = spec_dir / "causal_dag.json"
    tax_path = spec_dir / "metric_taxonomy.json"

    edges = load_dag(dag_path)
    taxonomy_raw = json.loads(tax_path.read_text(encoding="utf-8"))
    taxonomy = {m["metric_key"]: m for m in taxonomy_raw["metrics"]}

    dot = graphviz.Digraph(
        "causal_dag",
        format="svg",
        graph_attr={
            "rankdir": "LR",
            "nodesep": "0.4",
            "ranksep": "0.8",
            "fontname": "Helvetica",
            "bgcolor": "white",
        },
        node_attr={
            "shape": "box",
            "style": "filled,rounded",
            "fontsize": "10",
            "fontname": "Helvetica",
        },
        edge_attr={"fontname": "Helvetica", "fontsize": "8"},
    )

    nodes_added = set()
    for e in edges:
        for raw_key in (e.source, e.target):
            base = _strip_block_suffix(raw_key)
            if base in nodes_added:
                continue
            cluster = _cluster_for(base, taxonomy)
            color = CLUSTER_COLORS.get(cluster, "#cbd5e1")
            dot.node(base, label=_short_label(base), fillcolor=color)
            nodes_added.add(base)

    for e in edges:
        style = "dashed" if e.lag_turns >= 1 else "solid"
        color = SCOPE_EDGE_COLOR.get(e.scope, "#475569")
        thickness = MAGNITUDE_THICKNESS.get(e.magnitude, "1.0")
        arrowhead = "vee" if e.direction == "positive" else "tee"
        label = f"L{e.lag_turns}" if e.lag_turns >= 1 else ""
        dot.edge(
            e.base_source,
            e.base_target,
            style=style,
            color=color,
            penwidth=thickness,
            arrowhead=arrowhead,
            label=label,
        )

    out_dir = ROOT / "docs" / "causal_dag"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_base = out_dir / "diagram"

    dot_source = out_base.with_suffix(".dot")
    dot_source.write_text(dot.source, encoding="utf-8")
    print(f"wrote dot source: {dot_source}")

    for fmt in ("svg", "png"):
        dot.format = fmt
        try:
            dot.render(filename=out_base.name, directory=out_dir, cleanup=True)
            print(f"rendered: {out_base}.{fmt}")
        except graphviz.backend.execute.ExecutableNotFound:
            print(f"warning: graphviz binary not found; skipped .{fmt}")
            print("  install with `brew install graphviz` (macOS) or `apt install graphviz` (Linux)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
