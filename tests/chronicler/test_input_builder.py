"""Tests for src/chronicler/input_builder.py."""
from src.chronicler.discourse import Seed, get_lens_for_turn, load_seed_catalog, sample_discourse_seeds
from src.chronicler.input_builder import build_chronicler_input
from src.engine.simulation import Simulation


def _one_turn_artifacts():
    """Run the engine for one turn so we have a real TurnResult to feed in."""
    sim = Simulation.from_spec(seed=42)
    initial_state = sim.state
    result = sim.run_turn()
    return result, initial_state, result.state_after


def test_build_input_contains_required_sections():
    result, before, after = _one_turn_artifacts()
    catalog = load_seed_catalog()
    seeds = sample_discourse_seeds(
        turn_index=0, turn_label="1998-S1", seed=42, catalog=catalog
    )
    lens = get_lens_for_turn(turn_index=0, seed=42)
    out = build_chronicler_input(
        turn_result=result,
        state_before=before,
        state_after=after,
        narrative_history=[],
        lens=lens,
        seeds=seeds,
    )
    # Headers we expect to see
    assert "TURNO ATUAL:" in out
    assert "LENTE SOCIOLÓGICA" in out
    assert "ESTADO-MUNDO ANTES" in out
    assert "DELTAS COMPUTADOS" in out
    assert "CAUSAL_LINKS" in out
    assert "NARRATIVA ACUMULADA" in out
    # Lens text appears
    assert lens in out


def test_build_input_includes_seeds_text():
    result, before, after = _one_turn_artifacts()
    catalog = load_seed_catalog()
    seeds = sample_discourse_seeds(
        turn_index=0, turn_label="1998-S1", seed=42, catalog=catalog, n_seeds=4
    )
    out = build_chronicler_input(
        turn_result=result,
        state_before=before,
        state_after=after,
        narrative_history=[],
        lens="test lens",
        seeds=seeds,
    )
    if seeds:
        # First seed's text must appear
        assert seeds[0].text[:40] in out


def test_build_input_handles_empty_history():
    result, before, after = _one_turn_artifacts()
    out = build_chronicler_input(
        turn_result=result,
        state_before=before,
        state_after=after,
        narrative_history=[],
        lens="test",
        seeds=[],
    )
    assert "Primeiro turno" in out


def test_build_input_summarizes_old_history():
    """When history exceeds RECENT_NARRATIVE_WINDOW, older turns get summarized."""
    result, before, after = _one_turn_artifacts()
    history = [f"narrative for turn {i}. " * 10 for i in range(15)]
    out = build_chronicler_input(
        turn_result=result,
        state_before=before,
        state_after=after,
        narrative_history=history,
        lens="test",
        seeds=[],
    )
    assert "resumidos" in out


def test_build_input_includes_user_input_when_provided():
    result, before, after = _one_turn_artifacts()
    out = build_chronicler_input(
        turn_result=result,
        state_before=before,
        state_after=after,
        narrative_history=[],
        lens="test",
        seeds=[],
        user_input="Foque na crise financeira asiática.",
    )
    assert "crise financeira asiática" in out


def test_build_input_event_block_when_no_event():
    """Turn without an anchor event must say so explicitly."""
    result, before, after = _one_turn_artifacts()
    out = build_chronicler_input(
        turn_result=result,
        state_before=before,
        state_after=after,
        narrative_history=[],
        lens="test",
        seeds=[],
    )
    if result.sampled_event is None:
        assert "Nenhum evento histórico âncora" in out
