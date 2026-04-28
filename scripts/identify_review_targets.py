"""Identify edges in the causal DAG that need focused methodological review (Etapa 2).

Applies four criteria and emits a markdown file grouped by cluster:

1. direction_contested == true
2. magnitude == "strong"
3. Added in Rodada 3 AND touches health.* / science_rd.* / mental_wellbeing
4. Justification in edges_justifications.md contains "[verificar referência]"

Each edge is assigned to the cluster of its source metric so it lives in exactly
one issue. Output is written to docs/causal_dag/review_targets.md.

Usage:
    python scripts/identify_review_targets.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).parent.parent
DAG_PATH = ROOT / "spec" / "causal_dag.json"
TAXONOMY_PATH = ROOT / "spec" / "metric_taxonomy.json"
JUSTIFICATIONS_PATH = ROOT / "docs" / "causal_dag" / "edges_justifications.md"
OUTPUT_PATH = ROOT / "docs" / "causal_dag" / "review_targets.md"

BLOCKS = {"US", "EU", "CN", "RoW"}

# Map round identifier (parsed from etapa_1_5_note) to the PR that introduced it.
PR_BY_ROUND = {
    "rodada-1": "#2",
    "rodada-2": "#3",
    "rodada-3": "#4",
    "etapa-1": "#1",
}

CLUSTER_ORDER = [
    "tecnologia_ia",
    "economia",
    "sociedade",
    "informacao_ambiente",
    "politica",
    "conhecimento_saude",
]


def strip_block_suffix(metric_key: str) -> str:
    parts = metric_key.split(".")
    if len(parts) < 2:
        return metric_key
    last = parts[-1]
    if last in BLOCKS:
        return ".".join(parts[:-1])
    if "_" in last:
        a, _, b = last.partition("_")
        if a in BLOCKS and (b in BLOCKS or last.startswith("internal_")):
            return ".".join(parts[:-1])
    return metric_key


def edge_round(edge: dict) -> str:
    note = edge.get("etapa_1_5_note", "") or ""
    if "Rodada 3" in note:
        return "rodada-3"
    if "Rodada 2" in note:
        return "rodada-2"
    if "Rodada 1" in note:
        return "rodada-1"
    return "etapa-1"


def touches_underconnected(edge: dict) -> bool:
    """True if source or target is in health.* / science_rd.* (mental_wellbeing is health.mental_wellbeing)."""
    for raw in (edge["source"], edge["target"]):
        base = strip_block_suffix(raw)
        if base.startswith("health.") or base.startswith("science_rd."):
            return True
    return False


def extract_unverified_ref_edges(md_path: Path) -> Set[str]:
    """Returns set of edge ids whose justification section contains '[verificar referência]'."""
    text = md_path.read_text(encoding="utf-8")
    sections = re.split(r"^### ", text, flags=re.M)
    matched: Set[str] = set()
    for sec in sections[1:]:
        head_match = re.match(r"(e_\w+):", sec)
        if not head_match:
            continue
        eid = head_match.group(1)
        if "verificar referência" in sec:
            matched.add(eid)
    return matched


def classify(
    edges: List[dict],
    metric_to_cluster: Dict[str, str],
    unverified: Set[str],
) -> Dict[str, List[Tuple[dict, List[str]]]]:
    """Returns {cluster: [(edge, criteria), ...]} where criteria is a non-empty list."""
    by_cluster: Dict[str, List[Tuple[dict, List[str]]]] = defaultdict(list)
    for edge in edges:
        criteria: List[str] = []
        if edge.get("direction_contested"):
            criteria.append("direction_contested")
        if edge.get("magnitude") == "strong":
            criteria.append("strong")
        if edge_round(edge) == "rodada-3" and touches_underconnected(edge):
            criteria.append("underconnected")
        if edge["id"] in unverified:
            criteria.append("unverified_ref")
        if not criteria:
            continue
        cluster = metric_to_cluster.get(strip_block_suffix(edge["source"]), "unknown")
        by_cluster[cluster].append((edge, criteria))
    return by_cluster


def render_markdown(by_cluster: Dict[str, List[Tuple[dict, List[str]]]]) -> str:
    total = sum(len(v) for v in by_cluster.values())
    lines: List[str] = []
    lines.append("# Review Targets — Etapa 2")
    lines.append("")
    lines.append(
        "Edges identificadas para revisão metodológica focada na Etapa 2. "
        "Geradas automaticamente por `scripts/identify_review_targets.py`."
    )
    lines.append("")
    lines.append(f"**Total**: {total} edges (de ~130) em {len(by_cluster)} clusters.")
    lines.append("")
    lines.append("## Critérios aplicados")
    lines.append("")
    lines.append("- `direction_contested`: edges com `direction_contested: true` (decisão de direção pendente)")
    lines.append("- `strong`: magnitude `strong` (alto impacto se errada)")
    lines.append(
        "- `underconnected`: edges adicionadas na Rodada 3 cuja source ou target "
        "está em `health.*` ou `science_rd.*` (inclui `health.mental_wellbeing`)"
    )
    lines.append("- `unverified_ref`: justificativa em `edges_justifications.md` contém `[verificar referência]`")
    lines.append("")
    lines.append(
        "Cada edge é listada em exatamente um cluster — o cluster da métrica de "
        "**source**. O reviewer do cluster destino pode flaggar spillover concerns "
        "durante a sessão se quiser."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    for cluster in CLUSTER_ORDER:
        items = by_cluster.get(cluster, [])
        if not items:
            continue
        lines.append(f"## Cluster: `{cluster}` ({len(items)} edges)")
        lines.append("")
        for edge, criteria in sorted(items, key=lambda kv: kv[0]["id"]):
            round_ = edge_round(edge)
            pr = PR_BY_ROUND.get(round_, "?")
            lines.append(f"### {edge['id']}: `{edge['source']}` → `{edge['target']}`")
            lines.append("")
            lines.append(f"- **Cluster**: {cluster}")
            lines.append(f"- **Critério(s)**: {' / '.join(criteria)}")
            lines.append(f"- **Magnitude atual**: {edge['magnitude']}")
            direction = edge["direction"]
            if edge.get("direction_contested"):
                direction = f"{direction} (contested)"
            lines.append(f"- **Direção atual**: {direction}")
            lines.append(f"- **Lag atual**: {edge['lag_turns']} turnos")
            lines.append(f"- **Scope**: {edge['scope']}")
            lines.append(f"- **PR onde mora**: {pr} ({round_})")
            note = edge.get("etapa_1_5_note") or ""
            if note:
                short = note.replace("\n", " ").strip()
                if len(short) > 240:
                    short = short[:237] + "..."
                lines.append(f"- **Nota inline**: {short}")
            lines.append("- **Status revisão**: pending")
            lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    dag = json.loads(DAG_PATH.read_text(encoding="utf-8"))
    edges = dag["edges"]
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    metric_to_cluster = {m["metric_key"]: m["cluster"] for m in taxonomy["metrics"]}
    unverified = extract_unverified_ref_edges(JUSTIFICATIONS_PATH)

    by_cluster = classify(edges, metric_to_cluster, unverified)
    markdown = render_markdown(by_cluster)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")

    total = sum(len(v) for v in by_cluster.values())
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Total edges identified: {total} (out of {len(edges)})")
    print()
    print("Per-cluster breakdown:")
    for cluster in CLUSTER_ORDER:
        n = len(by_cluster.get(cluster, []))
        print(f"  {cluster}: {n}")
    print()
    print(f"Edges with [verificar referência]: {len(unverified)}")
    if unverified:
        print(f"  ids: {sorted(unverified)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
