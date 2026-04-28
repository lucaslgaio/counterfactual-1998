"""Build the user-message string for the chronicler from a TurnResult.

The chronicler receives:
- A snapshot of the world before this turn (key metrics)
- The event sampled (if any) with provenance
- The shock sampled (if any)
- The deltas computed (top movers)
- The causal_links the engine identified
- The sociological lens for this turn
- The 4 discourse seeds
- A truncated history of recent narratives

Output is a single formatted string ready to feed to Gemini.
"""
from __future__ import annotations

from typing import List, Optional

from src.chronicler.discourse import Seed
from src.engine.aggregation import aggregate
from src.engine.delta_computer import DeltaPackage
from src.engine.event_sampler import SampledEvent
from src.engine.shock_sampler import SampledShock
from src.engine.state import WorldState
from src.engine.turn_runner import TurnResult


# How many full prior narratives to keep verbatim. Older ones are condensed
# into a single paragraph to keep the prompt under ~9k tokens even at turn 58.
RECENT_NARRATIVE_WINDOW = 5
# Top-N most-impactful deltas to surface in the prompt (by absolute value).
TOP_DELTA_COUNT = 8


def _summarize_state(state: WorldState) -> str:
    """One-line-per-metric digest of the most-watched indicators."""
    g = state.global_metrics
    bm = state.block_metrics
    lines = []

    def _block_summary(metric_key: str, label: str) -> str:
        if metric_key not in bm:
            return ""
        sub = bm[metric_key]
        wm = aggregate(sub, "weighted_mean")
        return (
            f"  {label}: US={sub.get('US', 0):.1f} EU={sub.get('EU', 0):.1f} "
            f"CN={sub.get('CN', 0):.1f} RoW={sub.get('RoW', 0):.1f} "
            f"(weighted_mean={wm:.1f})"
        )

    lines.append(_block_summary("ai_capability.frontier_capability", "frontier_capability"))
    lines.append(_block_summary("ai_capability.population_penetration", "population_penetration"))
    lines.append(_block_summary("labor_market.automation_exposure", "automation_exposure"))
    lines.append(_block_summary("labor_market.employment_rate", "employment_rate"))
    lines.append(_block_summary("inequality.gini_intra_block", "gini_intra_block"))
    lines.append(_block_summary("governance.democracy_index", "democracy_index"))
    lines.append(_block_summary("information_ecosystem.disinformation_level", "disinformation_level"))

    lines.append(f"  global_index: {g.get('financial_markets.global_index', 0):.1f}")
    lines.append(f"  systemic_risk: {g.get('financial_markets.systemic_risk', 0):.1f}")
    lines.append(f"  top1pct_share: {g.get('inequality.top1pct_share', 0):.1f}")
    lines.append(f"  life_expectancy: {g.get('health.life_expectancy', 0):.1f}")
    lines.append(f"  co2_gt_year: {g.get('energy_climate.co2_gt_year', 0):.1f}")
    lines.append(f"  media_trust: {g.get('information_ecosystem.media_trust', 0):.1f}")

    return "\n".join(line for line in lines if line)


def _format_event(event: Optional[SampledEvent]) -> str:
    if event is None:
        return "Nenhum evento histórico âncora neste semestre."
    parts = [
        f"{event.event_id}",
        f"variante: '{event.variant_id}' (P_efetiva={event.effective_probability:.2f})",
        f"descrição: {event.description}",
    ]
    if event.modulator_log:
        mods = ", ".join(f"{k}={v:+.2f}" for k, v in event.modulator_log.items() if abs(v) > 0.001)
        if mods:
            parts.append(f"modulators: {mods}")
    return " | ".join(parts)


def _format_shock(shock: Optional[SampledShock]) -> str:
    if shock is None:
        return "Nenhum choque exógeno neste semestre."
    deltas = ", ".join(f"{k}={v:+.1f}" for k, v in shock.delta_package.items())
    return f"{shock.shock_id}: {shock.description} (deltas: {deltas})"


def _format_top_deltas(pkg: DeltaPackage, n: int = TOP_DELTA_COUNT) -> str:
    """Top |delta| across global, block, matrix layers."""
    rows = []
    for k, v in pkg.global_deltas.items():
        rows.append((f"global.{k}", v))
    for metric_key, by_block in pkg.block_deltas.items():
        for b, v in by_block.items():
            rows.append((f"{metric_key}.{b}", v))
    for metric_key, by_pair in pkg.matrix_deltas.items():
        for p, v in by_pair.items():
            rows.append((f"{metric_key}.{p}", v))
    rows.sort(key=lambda kv: -abs(kv[1]))
    top = rows[:n]
    if not top:
        return "  (sem deltas notáveis)"
    return "\n".join(f"  {k:<60} {v:+.3f}" for k, v in top)


def _format_causal_links(pkg: DeltaPackage) -> str:
    if not pkg.causal_links_active:
        return "  (motor não identificou causal_links destacáveis)"
    lines = []
    for c in pkg.causal_links_active:
        lines.append(
            f"  {c.edge_id}: {c.source} → {c.target} "
            f"(source_value={c.source_value:.2f}, contribution={c.contribution:+.3f}, form={c.form})"
        )
    return "\n".join(lines)


def _format_seeds(seeds: List[Seed]) -> str:
    if not seeds:
        return "  (sem sementes amostradas)"
    return "\n".join(f"  • ({s.year}, {s.domain}) {s.text}" for s in seeds)


def _format_narrative_history(history: List[str]) -> str:
    """Recent narratives verbatim; older ones condensed to a single paragraph."""
    if not history:
        return "(Primeiro turno — sem narrativa anterior.)"
    if len(history) <= RECENT_NARRATIVE_WINDOW:
        return "\n\n".join(f"[Turno {i+1}] {n}" for i, n in enumerate(history))
    older = history[: -RECENT_NARRATIVE_WINDOW]
    recent = history[-RECENT_NARRATIVE_WINDOW:]
    older_summary = (
        f"[Turnos 1-{len(older)} resumidos] "
        + " ".join(_first_sentence(n) for n in older)[:1500]
    )
    recent_block = "\n\n".join(
        f"[Turno {len(older) + i + 1}] {n}" for i, n in enumerate(recent)
    )
    return older_summary + "\n\n" + recent_block


def _first_sentence(text: str) -> str:
    """Quick & dirty first-sentence extractor."""
    for sep in [". ", ".\n", "; "]:
        if sep in text:
            return text.split(sep, 1)[0].strip() + "."
    return text[:120].strip()


# ---------------------------------------------------------------------------- public


def build_chronicler_input(
    turn_result: TurnResult,
    state_before: WorldState,
    state_after: WorldState,
    narrative_history: List[str],
    lens: str,
    seeds: List[Seed],
    user_input: Optional[str] = None,
) -> str:
    """Assemble the full prompt the chronicler will see for one turn.

    The motor's output is read-only here; the chronicler doesn't mutate it.
    """
    return f"""TURNO ATUAL: {turn_result.turn_label} (turn_index={turn_result.turn_index})

LENTE SOCIOLÓGICA DE FOCO PARA ESTE TURNO:
{lens}

SEMENTES DE DEBATE CONTEMPORÂNEO (matéria-prima pra transpor pra esta época):
{_format_seeds(seeds)}

ESTADO-MUNDO ANTES DO TURNO (resumo):
{_summarize_state(state_before)}

EVENTO HISTÓRICO ÂNCORA (motor amostrou):
  {_format_event(turn_result.sampled_event)}

CHOQUE EXÓGENO (motor amostrou):
  {_format_shock(turn_result.sampled_shock)}

DELTAS COMPUTADOS PELO MOTOR (top {TOP_DELTA_COUNT} por magnitude absoluta):
{_format_top_deltas(turn_result.delta_package)}

CAUSAL_LINKS QUE DISPARARAM (motor identificou):
{_format_causal_links(turn_result.delta_package)}

INPUT DO USUÁRIO (diretriz, se houver):
  {user_input or "Nenhum input do usuário; siga o que o motor calculou."}

NARRATIVA ACUMULADA (turnos anteriores):
{_format_narrative_history(narrative_history)}

LEMBRETE: você não decide o que aconteceu — o motor já decidiu. Você narra. \
Use a lente como ângulo de entrada e as sementes como matéria-prima concreta. \
Atores específicos, lugares específicos, organizações com nome, fatos consumados, \
tensões reais. Responda chamando a função `chronicle_turn`."""
