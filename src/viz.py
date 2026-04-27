"""Visualizações: sparklines, setas de magnitude, árvore causal."""
from __future__ import annotations

from typing import List

from rich.tree import Tree

from src.glossary import BAD_WHEN_UP


SPARK_CHARS = "▁▂▃▄▅▆▇█"


def sparkline(values: List[float]) -> str:
    """Sparkline ASCII a partir de uma lista de valores."""
    if not values:
        return ""
    if len(values) == 1:
        return SPARK_CHARS[3]
    lo, hi = min(values), max(values)
    if hi == lo:
        return SPARK_CHARS[3] * len(values)
    out = []
    for v in values:
        idx = int((v - lo) / (hi - lo) * (len(SPARK_CHARS) - 1))
        out.append(SPARK_CHARS[idx])
    return "".join(out)


def magnitude_arrow(delta: float, scale: tuple = (0.5, 2.0, 6.0)) -> str:
    """Retorna setas indicando direção e magnitude do delta.

    Faixas (default): <0.5 = ↑/↓, <2 = ↑↑/↓↓, <6 = ↑↑↑/↓↓↓, ≥6 = ↑↑↑↑/↓↓↓↓.
    """
    if delta == 0:
        return "·"
    abs_d = abs(delta)
    char = "↑" if delta > 0 else "↓"
    if abs_d < scale[0]:
        return char
    if abs_d < scale[1]:
        return char * 2
    if abs_d < scale[2]:
        return char * 3
    return char * 4


def delta_color(metric_key: str, delta: float) -> str:
    """Cor do delta levando em conta a polaridade da métrica."""
    metric_name = metric_key.split(".")[-1] if "." in metric_key else metric_key
    if metric_name in BAD_WHEN_UP:
        return "red" if delta >= 0 else "green"
    return "green" if delta >= 0 else "red"


def render_causal_tree(causal_links) -> Tree:
    """Renderiza causal_links como árvore Rich, agrupando por fonte."""
    tree = Tree("[bold cyan]links causais deste turno[/bold cyan]")
    if not causal_links:
        tree.add("[dim](sem links declarados)[/dim]")
        return tree

    by_source: dict[str, list] = {}
    for link in causal_links:
        by_source.setdefault(link.source, []).append(link)

    for source, group in by_source.items():
        branch = tree.add(f"[bold yellow]{source}[/bold yellow]")
        for link in group:
            arrow = "↑" if link.direction == "up" else "↓"
            color = delta_color(link.target, 1.0 if link.direction == "up" else -1.0)
            branch.add(f"[{color}]{link.target} {arrow}[/{color}]")
    return tree
