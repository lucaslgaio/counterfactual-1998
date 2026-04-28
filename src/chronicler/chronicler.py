"""Public chronicler API.

Workflow:
    client = GeminiClient.from_env()
    session = ChroniclerSession(client=client, seed=42)

    # Run engine first (motor SDM):
    sim = Simulation.from_spec(seed=42)
    results = sim.run_many(58)

    # Chronicle each turn:
    chronicled = []
    states = [results[0].state_before] + [r.state_after for r in results]
    for i, r in enumerate(results):
        out = session.chronicle_turn(r, states[i], states[i + 1])
        chronicled.append(out)

ChroniclerSession holds the narrative_history (used to keep cross-turn
coherence) and the seed (used by the discourse module).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from src.chronicler.discourse import (
    Seed,
    get_lens_for_turn,
    load_seed_catalog,
    sample_discourse_seeds,
)
from src.chronicler.gemini_client import GeminiClient
from src.chronicler.input_builder import build_chronicler_input
from src.chronicler.output_parser import (
    ChroniclerOutput,
    ChroniclerOutputError,
    parse_chronicler_response,
)
from src.chronicler.prompts import CHRONICLER_SYSTEM_PROMPT
from src.chronicler.retry import (
    MalformedResponseError,
    RetryConfig,
    with_retry,
)
from src.engine.state import WorldState
from src.engine.turn_runner import TurnResult

logger = logging.getLogger(__name__)


@dataclass
class ChroniclerSession:
    """One narrative pass over a Simulation's history.

    Holds rolling narrative_history that gets fed back into each turn's
    prompt so the chronicle stays coherent across the 58 turns.
    """

    client: GeminiClient
    seed: int = 42
    narrative_history_max_turns: int = 10
    seed_catalog: Optional[List[Seed]] = None
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    narrative_history: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.seed_catalog is None:
            try:
                self.seed_catalog = load_seed_catalog()
            except FileNotFoundError:
                logger.warning("discourse_seeds.json not found; chronicler will run without seeds")
                self.seed_catalog = []

    # ------------------------------------------------------------------ single turn

    def chronicle_turn(
        self,
        turn_result: TurnResult,
        state_before: WorldState,
        state_after: WorldState,
        user_input: Optional[str] = None,
    ) -> ChroniclerOutput:
        """Generate a chronicle for one turn.

        Determines the lens and seeds for this turn, builds the input
        prompt, calls Gemini with retry, parses the response, and appends
        the narrative to the session history.
        """
        lens = get_lens_for_turn(turn_result.turn_index, self.seed)
        seeds = sample_discourse_seeds(
            turn_index=turn_result.turn_index,
            turn_label=turn_result.turn_label,
            seed=self.seed,
            catalog=self.seed_catalog or [],
            n_seeds=4,
        )

        user_input_str = build_chronicler_input(
            turn_result=turn_result,
            state_before=state_before,
            state_after=state_after,
            narrative_history=self.narrative_history,
            lens=lens,
            seeds=seeds,
            user_input=user_input,
        )

        expected_event = turn_result.sampled_event is not None

        # Retry-aware call. Lower temperature on retry after malformed.
        def _attempt(temperature: float) -> ChroniclerOutput:
            args = self.client.call_chronicler(
                system_prompt=CHRONICLER_SYSTEM_PROMPT,
                user_input=user_input_str,
                temperature=temperature,
            )
            metadata = args.pop("_metadata", {})
            metadata["lens"] = lens
            metadata["seeds_count"] = len(seeds)
            try:
                return parse_chronicler_response(
                    args, expected_event_outcome=expected_event, metadata=metadata
                )
            except ChroniclerOutputError as exc:
                raise MalformedResponseError(str(exc)) from exc

        # We do up to 3 retries; second/third attempts use lower temperature.
        attempts: List[float] = [
            0.85,
            self.retry_config.temperature_after_malformed,
            self.retry_config.temperature_after_malformed,
        ]
        last_exc: Optional[Exception] = None
        for i, temp in enumerate(attempts[: self.retry_config.max_retries + 1]):
            try:
                output = _attempt(temp)
                self._update_history(output.narrative)
                return output
            except MalformedResponseError as exc:
                last_exc = exc
                logger.warning("chronicler attempt %d malformed: %s", i + 1, exc)
                if i == self.retry_config.max_retries:
                    raise
            except Exception:
                # Other exception types (TransientError, SafetyFilterError, PermanentError)
                # are handled by the underlying client.
                raise

        # Should not reach here unless all attempts malformed.
        raise last_exc or MalformedResponseError("chronicler exhausted attempts")

    # ------------------------------------------------------------------ batch

    def chronicle_run(
        self,
        turn_results: List[TurnResult],
        states: List[WorldState],
    ) -> List[ChroniclerOutput]:
        """Chronicle a full simulation run.

        ``states`` must be ``[state_at_start] + [r.state_after for r in turn_results]``,
        so that ``states[i]`` is before turn ``i`` and ``states[i+1]`` is after.
        """
        if len(states) != len(turn_results) + 1:
            raise ValueError(
                f"states must have len(turn_results)+1 elements; got "
                f"{len(states)} states and {len(turn_results)} turn_results"
            )
        out: List[ChroniclerOutput] = []
        for i, r in enumerate(turn_results):
            chronicled = self.chronicle_turn(
                turn_result=r,
                state_before=states[i],
                state_after=states[i + 1],
            )
            out.append(chronicled)
        return out

    # ------------------------------------------------------------------ internals

    def _update_history(self, narrative: str) -> None:
        self.narrative_history.append(narrative)
        # Cap memory; older narratives are summarized in input_builder.
        if len(self.narrative_history) > self.narrative_history_max_turns * 2:
            # Keep the most recent ones. input_builder handles truncation/summarization
            # but we don't want to grow unbounded across very long runs.
            self.narrative_history = self.narrative_history[-self.narrative_history_max_turns * 2 :]
