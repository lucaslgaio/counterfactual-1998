"""Smoke test multi-turno com UX game-like.

Uso:
    python -m src.smoke_test                       # 1 turno
    python -m src.smoke_test --turns 4             # 4 turnos com pause/input entre eles
    python -m src.smoke_test --turns 4 --auto      # 4 turnos sem pause/input
    python -m src.smoke_test --turns 4 --seed 42   # reprodutibilidade
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.config import SimulationConfig
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


DATA_DIR = Path(__file__).parent.parent / "data"

# Métricas onde "subir" significa piora — pra colorir deltas contextualmente.
BAD_WHEN_UP = {
    "systemic_risk",
    "automation_exposure",
    "global_gini",
    "top1pct_share",
    "active_conflicts",
    "disinformation_level",
    "co2_gt_year",
    "cost_index",
    "bigtech_concentration",
}

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


# =============================================================================
# Componentes de UI
# =============================================================================


def show_intro(console: Console, config: SimulationConfig, num_turns: int) -> None:
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
        deltas_table.add_column("métrica", style="dim")
        deltas_table.add_column("Δ", justify="right")

        for k, v in sorted(response.deltas.items(), key=lambda kv: -abs(kv[1])):
            metric_name = k.split(".")[-1]
            sign = "+" if v >= 0 else ""
            if metric_name in BAD_WHEN_UP:
                color = "red" if v >= 0 else "green"
            else:
                color = "green" if v >= 0 else "red"
            deltas_table.add_row(k, f"[{color}]{sign}{v:.2f}[/{color}]")
        console.print(deltas_table)
        console.print()

    console.print(f"[dim]confiança do motor: {response.confidence}[/dim]")


def show_outro(
    console: Console, initial_state: State, final_state: State, num_turns: int
) -> None:
    console.print()
    console.print()
    console.rule(
        f"[bold cyan]FIM DA SIMULAÇÃO[/bold cyan]  ·  {num_turns} turnos rodados",
        style="cyan",
    )
    console.print()

    init = initial_state.model_dump(exclude={"turn", "config"})
    final = final_state.model_dump(exclude={"turn", "config"})

    rows = []
    for dim in init:
        for metric, init_val in init[dim].items():
            final_val = final[dim][metric]
            delta = final_val - init_val
            pct = (delta / init_val * 100) if init_val else 0.0
            rows.append((f"{dim}.{metric}", init_val, final_val, delta, pct))

    rows.sort(key=lambda r: -abs(r[4]))

    table = Table(title="maiores mudanças do início ao fim")
    table.add_column("métrica", style="cyan")
    table.add_column("inicial", justify="right", style="dim")
    table.add_column("final", justify="right", style="bold")
    table.add_column("Δ", justify="right")
    table.add_column("Δ%", justify="right")

    for k, init_val, final_val, delta, pct in rows[:10]:
        metric_name = k.split(".")[-1]
        sign = "+" if delta >= 0 else ""
        if metric_name in BAD_WHEN_UP:
            color = "red" if delta >= 0 else "green"
        else:
            color = "green" if delta >= 0 else "red"
        table.add_row(
            k,
            f"{init_val:.2f}",
            f"{final_val:.2f}",
            f"[{color}]{sign}{delta:.2f}[/{color}]",
            f"[{color}]{sign}{pct:.1f}%[/{color}]",
        )

    console.print(table)
    console.print()
    console.print(f"[dim]turno final: {final_state.turn}[/dim]")
    console.print()


# =============================================================================
# Loop principal
# =============================================================================


def run(num_turns: int, auto: bool, seed: Optional[int]) -> None:
    load_dotenv()
    console = Console()

    config_kwargs = {}
    if seed is not None:
        config_kwargs["seed"] = seed
    config = SimulationConfig(**config_kwargs)

    show_intro(console, config, num_turns)

    state = load_initial_state(config)
    initial_state = state
    events = load_events()
    narrative_history: list[str] = []
    client = get_client()

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

        if i < num_turns - 1 and not auto:
            console.print()
            try:
                raw = console.input(
                    "[dim]→ Enter para próximo turno  ·  ou digite uma diretriz:[/dim] "
                )
            except EOFError:
                raw = ""
            user_input_for_next = raw.strip() or None

    show_outro(console, initial_state, state, num_turns)


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
    args = parser.parse_args()

    run(num_turns=args.turns, auto=args.auto, seed=args.seed)


if __name__ == "__main__":
    main()
