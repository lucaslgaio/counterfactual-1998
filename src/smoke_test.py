"""Smoke test multi-turno com UX game-like.

Uso:
    python -m src.smoke_test                       # 1 turno
    python -m src.smoke_test --turns 4             # 4 turnos com pause/input entre eles
    python -m src.smoke_test --turns 4 --auto      # 4 turnos sem pause/input
    python -m src.smoke_test --turns 4 --manual    # mostra glossário das 24 métricas antes
    python -m src.smoke_test --turns 4 --seed 42   # reprodutibilidade
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.config import SimulationConfig
from src.glossary import METRICS, METRICS_LIST, metrics_by_cluster
from src.llm import get_client, simulate_turn
from src.models import (
    ExogenousShock,
    HistoricalEvent,
    State,
    TurnResponse,
    advance_turn,
    apply_deltas,
)
from src.shocks import maybe_generate_shock
from src.viz import delta_color, magnitude_arrow, render_causal_tree, sparkline


DATA_DIR = Path(__file__).parent.parent / "data"

SEVERITY_COLOR = {
    "low": "white",
    "medium": "yellow",
    "high": "orange3",
    "critical": "red",
}


# =============================================================================
# Carregadores
# =============================================================================


def load_initial_state(config: SimulationConfig, turn: str = "1998-S1") -> State:
    raw = json.loads((DATA_DIR / "initial_state.json").read_text(encoding="utf-8"))
    raw["ai_capability"]["population_penetration"] = config.initial_population_penetration
    return State(turn=turn, config=config, **raw)


def load_events() -> dict:
    raw = json.loads((DATA_DIR / "historical_events.json").read_text(encoding="utf-8"))
    return {e["date"]: HistoricalEvent(**e) for e in raw}


def state_metric_value(state: State, metric_key: str) -> float:
    dim, metric = metric_key.split(".", 1)
    return float(getattr(getattr(state, dim), metric))


# =============================================================================
# Componentes de UI
# =============================================================================


def show_manual(console: Console) -> None:
    """Mostra glossário das 24 métricas, agrupadas por cluster."""
    console.clear()
    console.print()
    console.print(Align.center(Text("MANUAL DAS 24 MÉTRICAS", style="bold cyan")))
    console.print(Align.center(Text("como ler o estado do mundo", style="dim italic")))
    console.print()

    for cluster, metrics_list in metrics_by_cluster().items():
        body = Table(show_header=False, box=None, padding=(0, 1), show_edge=False)
        body.add_column(style="bold cyan", width=28, no_wrap=False)
        body.add_column(style="white")

        for m in metrics_list:
            anchors = "\n".join(
                f"  [yellow]{val:g}[/yellow] [dim]·[/dim] {meaning}"
                for val, meaning in m.anchors
            )
            content = (
                f"[dim]{m.description}[/dim]\n"
                f"[dim]faixa: {m.range_label}[/dim]\n"
                f"{anchors}"
            )
            body.add_row(m.short_label, content)

        console.print(Panel(
            body,
            title=f"[bold]{cluster}[/bold]",
            border_style="cyan",
            padding=(0, 1),
        ))

    console.print()
    try:
        console.input("[dim]  Pressione Enter para iniciar a simulação...[/dim] ")
    except EOFError:
        pass
    console.clear()


def show_intro(
    console: Console,
    config: SimulationConfig,
    num_turns: int,
    showed_manual: bool,
) -> None:
    if not showed_manual:
        console.clear()
    console.print()
    console.print()

    title = Text()
    title.append("COUNTERFACTUAL", style="bold cyan")
    title.append(" // 1998", style="bold yellow")
    subtitle = Text("um simulador de mundos que não foram", style="dim italic")

    console.print(Align.center(title))
    console.print(Align.center(subtitle))
    console.print()

    premise = Text()
    premise.append("Em S1 de 1998, uma inteligência artificial equivalente ao Claude 4 emerge ", style="white")
    premise.append("subitamente", style="bold cyan")
    premise.append(".\n", style="white")
    premise.append("Os próximos 28 anos do mundo serão recontados em semestres pelo motor causal.\n\n", style="white")
    premise.append("A história real é o ", style="dim")
    premise.append("ground truth", style="dim italic cyan")
    premise.append(" — mas eventos podem ser ", style="dim")
    premise.append("alterados, anulados ou substituídos", style="dim yellow")
    premise.append("\nquando o estado contrafactual os tornar implausíveis.", style="dim")

    console.print(Panel(
        premise,
        border_style="cyan",
        padding=(1, 4),
        width=min(console.width - 4, 90),
    ))

    if not showed_manual:
        console.print()
        console.print(Align.center(Text(
            "dica: rode com --manual pra ver o glossário das 24 métricas",
            style="dim italic",
        )))

    console.print()

    cfg_grid = Table.grid(padding=(0, 2))
    cfg_grid.add_column(style="dim", justify="right")
    cfg_grid.add_column(style="bold")
    cfg_grid.add_row("ai_mode", config.ai_mode)
    cfg_grid.add_row("play_mode", config.play_mode)
    cfg_grid.add_row("turnos a rodar", str(num_turns))
    cfg_grid.add_row("temperature", f"{config.temperature}")
    cfg_grid.add_row("p(choque exógeno)", f"{config.random_shock_probability:.0%}")
    cfg_grid.add_row("seed", str(config.seed))
    cfg_grid.add_row("model", config.model)
    cfg_grid.add_row("acesso à IA em S1/98", f"{config.initial_population_penetration}% da população")

    console.print(Panel(
        Align.center(cfg_grid),
        title="[dim]configuração da run[/dim]",
        border_style="dim",
        padding=(0, 2),
        width=min(console.width - 4, 90),
    ))

    console.print()
    try:
        console.input("  [dim]Pressione Enter para iniciar a simulação...[/dim] ")
    except EOFError:
        pass

    console.clear()


def show_turn_header(
    console: Console,
    state: State,
    event: Optional[HistoricalEvent],
    shock: Optional[ExogenousShock],
    turn_num: int,
    total: int,
) -> None:
    console.print()
    header = Text()
    header.append(f"TURNO {turn_num}/{total}", style="bold cyan")
    header.append("  ·  ", style="dim")
    header.append(state.turn, style="bold yellow")
    console.rule(header, style="cyan")
    console.print()

    if event:
        sev_color = SEVERITY_COLOR.get(event.severity, "white")
        body = Text()
        body.append(event.name, style="bold")
        body.append("\nseveridade: ", style="dim")
        body.append(event.severity, style=sev_color)
        body.append("  ·  domínio: ", style="dim")
        body.append(event.domain, style="dim white")
        console.print(Panel(
            body,
            title="[bold red]evento histórico real deste semestre[/bold red]",
            border_style=sev_color,
            padding=(0, 2),
        ))

    if shock:
        body = Text()
        body.append(shock.name, style="bold magenta")
        body.append(f"\n{shock.description}", style="dim")
        body.append("\nseveridade: ", style="dim")
        body.append(shock.severity, style="magenta")
        body.append("  ·  domínio: ", style="dim")
        body.append(shock.domain, style="dim white")
        console.print(Panel(
            body,
            title="[bold magenta]choque exógeno (não-histórico)[/bold magenta]",
            border_style="magenta",
            padding=(0, 2),
        ))

    if not event and not shock:
        console.print("[dim]  (semestre sem eventos âncora nem choques exógenos)[/dim]")


def show_response(console: Console, response: TurnResponse, state: State) -> None:
    """Narrativa, key developments, event outcome, deltas (com unidade) e árvore causal."""
    console.print()
    console.print(Panel(
        response.narrative,
        title=f"[cyan]crônica de {state.turn}[/cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()

    console.print("[bold]desenvolvimentos:[/bold]")
    for dev in response.key_developments:
        console.print(f"  [cyan]▸[/cyan] {dev}")
    console.print()

    if response.event_outcome != "N/A":
        outcome_color = {"ocorreu": "green", "alterado": "yellow", "anulado": "red"}.get(
            response.event_outcome, "white"
        )
        line = Text()
        line.append("evento histórico: ", style="bold")
        line.append(response.event_outcome, style=f"bold {outcome_color}")
        console.print(line)
        if response.event_outcome_explanation:
            console.print(f"  [dim]{response.event_outcome_explanation}[/dim]")
        console.print()

    if response.deltas:
        deltas_table = Table(
            title="[bold]deltas aplicados[/bold]",
            box=None,
            show_header=False,
            padding=(0, 1),
            title_justify="left",
        )
        deltas_table.add_column("métrica", style="dim", no_wrap=True)
        deltas_table.add_column("Δ", justify="right", no_wrap=True)
        deltas_table.add_column("magnitude", no_wrap=True)
        deltas_table.add_column("descrição", style="white")

        for k, v in sorted(response.deltas.items(), key=lambda kv: -abs(kv[1])):
            color = delta_color(k, v)
            info = METRICS.get(k)
            delta_str = info.format_delta(v) if info else f"{v:+.2f}"
            label = info.short_label if info else k.split(".")[-1]
            arrow = magnitude_arrow(v)
            deltas_table.add_row(
                label,
                f"[{color}]{delta_str}[/{color}]",
                f"[{color}]{arrow}[/{color}]",
                f"[dim]{k}[/dim]",
            )
        console.print(deltas_table)
        console.print()

    if response.causal_links:
        console.print(render_causal_tree(response.causal_links))
        console.print()

    console.print(f"[dim]confiança do motor: {response.confidence}[/dim]")


def show_outro(
    console: Console,
    initial_state: State,
    final_state: State,
    metric_history: dict[str, list[float]],
    num_turns: int,
) -> None:
    console.print()
    console.print()
    console.rule(
        f"[bold cyan]FIM DA SIMULAÇÃO[/bold cyan]  ·  {num_turns} turnos rodados",
        style="cyan",
    )
    console.print()

    # Calcula deltas acumulados
    rows = []
    for key, info in METRICS.items():
        before = state_metric_value(initial_state, key)
        after = state_metric_value(final_state, key)
        delta = after - before
        pct = (delta / before * 100) if before else 0.0
        rows.append((key, info, before, after, delta, pct))

    # Ordena por |Δ%|
    rows.sort(key=lambda r: -abs(r[5]))

    # ── Top mudanças com prosa ─────────────────────────────────────────────
    console.print("[bold]o que mais mudou[/bold]\n")
    for key, info, before, after, delta, pct in rows[:8]:
        if abs(delta) < 0.01:
            continue
        color = delta_color(key, delta)
        arrow = magnitude_arrow(delta)
        sign = "+" if pct >= 0 else ""
        prose = info.interpret(before, after)
        console.print(f"  [{color}]{arrow}[/{color}]  {prose}  [dim]({sign}{pct:.1f}%)[/dim]")
    console.print()

    # ── Sparklines por cluster ─────────────────────────────────────────────
    console.print("[bold]trajetória das métricas[/bold]\n")
    for cluster, metrics_list in metrics_by_cluster().items():
        cluster_table = Table(
            box=None, show_header=False, padding=(0, 1), title_justify="left"
        )
        cluster_table.add_column(style="dim", width=28)
        cluster_table.add_column(no_wrap=True)
        cluster_table.add_column(justify="right", style="bold")

        for m in metrics_list:
            history = metric_history.get(m.key, [])
            if not history:
                continue
            spark = sparkline(history)
            initial = history[0]
            final = history[-1]
            color = delta_color(m.key, final - initial)
            cluster_table.add_row(
                m.short_label,
                f"[{color}]{spark}[/{color}]",
                f"{initial:.2f} → {final:.2f}",
            )

        console.print(Panel(
            cluster_table,
            title=f"[cyan]{cluster}[/cyan]",
            border_style="dim",
            padding=(0, 1),
        ))
    console.print()
    console.print(f"[dim]turno final: {final_state.turn}[/dim]")
    console.print()


# =============================================================================
# Loop principal
# =============================================================================


def run(num_turns: int, auto: bool, seed: Optional[int], show_manual_flag: bool) -> None:
    load_dotenv()
    console = Console()

    config_kwargs = {}
    if seed is not None:
        config_kwargs["seed"] = seed
    config = SimulationConfig(**config_kwargs)

    if show_manual_flag:
        show_manual(console)
    show_intro(console, config, num_turns, showed_manual=show_manual_flag)

    state = load_initial_state(config)
    initial_state = state
    events = load_events()
    narrative_history: list[str] = []
    client = get_client()

    # Histórico de cada métrica pra sparklines
    metric_history: dict[str, list[float]] = defaultdict(list)
    for key in METRICS:
        metric_history[key].append(state_metric_value(state, key))

    user_input_for_next: Optional[str] = None

    for i in range(num_turns):
        event = events.get(state.turn)
        shock = maybe_generate_shock(state.turn, config)

        show_turn_header(console, state, event, shock, i + 1, num_turns)

        with console.status(
            f"[cyan]o motor causal está raciocinando sobre {state.turn}...[/cyan]",
            spinner="dots",
        ):
            response = simulate_turn(
                client=client,
                state=state,
                event=event,
                shock=shock,
                user_input=user_input_for_next,
                narrative_history=narrative_history,
                config=config,
            )

        show_response(console, response, state)

        state = apply_deltas(state, response.deltas)
        state = state.model_copy(update={"turn": advance_turn(state.turn)})
        narrative_history.append(response.narrative)
        user_input_for_next = None

        for key in METRICS:
            metric_history[key].append(state_metric_value(state, key))

        if i < num_turns - 1 and not auto:
            console.print()
            try:
                raw = console.input(
                    "[dim]→ Enter para próximo turno  ·  ou digite uma diretriz:[/dim] "
                )
            except EOFError:
                raw = ""
            user_input_for_next = raw.strip() or None

    show_outro(console, initial_state, state, metric_history, num_turns)


def main() -> None:
    parser = argparse.ArgumentParser(description="Roda a simulação contrafactual.")
    parser.add_argument("--turns", type=int, default=1, help="Número de turnos (default: 1)")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Não pausa nem pede input entre turnos",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed pra reprodutibilidade (default: aleatória)",
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Mostra glossário das 24 métricas antes da simulação",
    )
    args = parser.parse_args()

    run(
        num_turns=args.turns,
        auto=args.auto,
        seed=args.seed,
        show_manual_flag=args.manual,
    )


if __name__ == "__main__":
    main()
