"""Smoke test: roda 1 turno end-to-end e imprime o resultado.

Uso:
    python -m src.smoke_test
"""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config import SimulationConfig
from src.llm import get_client, simulate_turn
from src.models import HistoricalEvent, State, apply_deltas
from src.shocks import maybe_generate_shock


DATA_DIR = Path(__file__).parent.parent / "data"


def load_initial_state(config: SimulationConfig, turn: str = "1998-S1") -> State:
    raw = json.loads((DATA_DIR / "initial_state.json").read_text(encoding="utf-8"))
    raw["ai_capability"]["population_penetration"] = config.initial_population_penetration
    return State(turn=turn, config=config, **raw)


def load_events() -> dict[str, HistoricalEvent]:
    raw = json.loads((DATA_DIR / "historical_events.json").read_text(encoding="utf-8"))
    return {e["date"]: HistoricalEvent(**e) for e in raw}


def render_state(console: Console, state: State, title: str) -> None:
    table = Table(title=title)
    table.add_column("Dimensão", style="cyan")
    table.add_column("Métrica", style="white")
    table.add_column("Valor", justify="right", style="green")

    state_dict = state.model_dump(exclude={"turn", "config"})
    for dim, metrics in state_dict.items():
        for metric, value in metrics.items():
            value_str = f"{value:.2f}" if isinstance(value, float) else str(value)
            table.add_row(dim, metric, value_str)
    console.print(table)


def main() -> None:
    load_dotenv()
    console = Console()

    console.rule("[bold]Smoke Test — Counterfactual-1998")

    config = SimulationConfig()
    console.print(
        f"[dim]Config: ai_mode={config.ai_mode}, seed={config.seed}, "
        f"temperature={config.temperature}, model={config.model}[/dim]\n"
    )

    state = load_initial_state(config)
    events = load_events()

    event = events.get(state.turn)
    shock = maybe_generate_shock(state.turn, config)

    console.print(f"[bold]Turno:[/bold] {state.turn}")
    console.print(f"[bold]Evento histórico:[/bold] {event.name if event else '(nenhum)'}")
    console.print(f"[bold]Choque exógeno:[/bold] {shock.name if shock else '(nenhum)'}\n")

    console.print("[dim]Chamando API Anthropic...[/dim]")
    client = get_client()
    response = simulate_turn(
        client=client,
        state=state,
        event=event,
        shock=shock,
        user_input=None,
        narrative_history=[],
        config=config,
    )

    console.print()
    console.print(Panel(response.narrative, title=f"Narrativa — {state.turn}", border_style="cyan"))

    console.print("\n[bold]Key developments:[/bold]")
    for dev in response.key_developments:
        console.print(f"  • {dev}")

    console.print(f"\n[bold]Event outcome:[/bold] {response.event_outcome}")
    if response.event_outcome_explanation:
        console.print(f"  [dim]{response.event_outcome_explanation}[/dim]")

    console.print(f"\n[bold]Confidence:[/bold] {response.confidence}")

    console.print("\n[bold]Deltas:[/bold]")
    if not response.deltas:
        console.print("  [dim](nenhum)[/dim]")
    else:
        for k, v in sorted(response.deltas.items()):
            sign = "+" if v >= 0 else ""
            console.print(f"  {k}: [yellow]{sign}{v:.3f}[/yellow]")

    new_state = apply_deltas(state, response.deltas)

    console.print()
    render_state(console, new_state, f"Estado após {state.turn} (deltas aplicados)")


if __name__ == "__main__":
    main()
