# Chronicler prompt design

## Background

The original `src/llm.py` + `src/prompts.py` operated the LLM as the
**simulator**: it decided deltas, sampled events, identified causal links,
and wrote narrative — all in one function call. That worked at small scale
but had problems:

1. **Numerical drift**: the LLM picks deltas that feel right narratively
   but don't accumulate to coherent trajectories across 58 turns.
2. **Causal inconsistency**: nothing forces the LLM to reuse the same
   causal_link from one turn to the next; mechanisms appear and disappear.
3. **Calibration impossible**: there's no way to fit alphas to data when
   the LLM's stochastic prose is also driving the numbers.

The engine in `src/engine/` (Etapa 4) plus calibration (Etapa 5) solve
1-3 by making the numerical layer deterministic, structured, and
parameter-fittable. The chronicler then handles only the prose.

## Division of labor

| Concern                    | Owner       |
|----------------------------|-------------|
| Compute deltas             | Engine SDM  |
| Sample event variants      | Engine SDM  |
| Sample exogenous shocks    | Engine SDM  |
| Identify causal_links      | Engine SDM  |
| Apply ranges & clamps      | Engine SDM  |
| Pick sociological lens     | Chronicler  |
| Sample discourse seeds     | Chronicler  |
| Write narrative            | Chronicler  |
| Explain event outcome      | Chronicler  |
| Subjective confidence      | Chronicler  |

## What was preserved from the old prompt

The voice is unchanged. The rich tone — sociological cronista, specific
actors, named organizations, transposed contemporary debates — was the
*best* part of the original. We kept it verbatim:

- "DEBATES CONTEMPORÂNEOS COMO MATÉRIA-PRIMA" list
- Bad-example / good-example pair
- "VETOS" list of forbidden phrases
- "ESTRUTURA DA NARRATIVA" guidance

## What changed

The functional instructions were rewritten:

| Old prompt                                            | New prompt                                              |
|-------------------------------------------------------|---------------------------------------------------------|
| "Decide deltas. 80-200 palavras."                     | "Você NÃO decide. Narra 150-300 palavras."              |
| "Identifique 3-8 causal_links."                       | "Use os causal_links que o motor identificou."         |
| "Eventos podem ser ocorreu/alterado/anulado."         | "Eventos vêm do motor. Você apenas narra a variante."   |
| "Choques exógenos quando presentes incorpore."        | Same — but they come from the engine.                   |
| Function name: `advance_turn`                         | Function name: `chronicle_turn`                         |
| Schema includes `deltas` (array)                      | Schema does NOT include `deltas` — engine owns these.   |
| Schema includes `causal_links` (array)                | Schema does NOT include `causal_links` — engine owns.  |

Reduction in schema size matters: fewer fields to validate, fewer ways
the LLM can return malformed output, fewer hallucination surfaces.

## Why narrative is 150-300 words (vs 80-200 before)

The chronicler has more *context* to work with now (every causal_link the
engine identified is in the input prompt). 80 words wasn't enough to do
justice to the structured causal information. 300 caps prose-length so a
single turn doesn't dominate the chronicle.

## Why temperature 0.85

Empirically: lower temperatures (≤0.5) produced bland, repetitive prose.
Higher (≥0.95) made the chronicler invent organizations and events. 0.85
is the sweet spot for densely-named-actor prose without crossing into
fabrication.

On retry after malformed output, we drop to 0.7 — the parser is more
likely to accept a structured response from a more-deterministic call.

## Why thinking_budget=0

The original `src/llm.py` had this lesson learned the hard way: Gemini
2.5+ has reasoning enabled by default, which consumes tokens from
`max_output_tokens` *before* the function call lands. With our 2048 budget,
reasoning often ate the entire allotment and the function call came back
truncated as MALFORMED_FUNCTION_CALL.

`thinking_budget=0` is mandatory for the chronicler's contract.

## Why BLOCK_ONLY_HIGH on all 4 safety categories

Historical content trips standard thresholds: wars, financial crises,
deaths-of-despair statistics, ideological extremism — all standard fare
for a 1998-2026 chronicle. Without relaxing the filter, ~10% of turns get
blocked unnecessarily. We don't disable filters (BLOCK_ONLY_HIGH still
catches genuinely harmful content), just relax them to fit the use case.

## Open questions / future iterations

1. **Cross-turn voice consistency**: even with narrative_history in the
   prompt, the chronicler's voice drifts slightly turn-by-turn. A
   per-session "voice anchor" in the system prompt may help.
2. **Per-block narration**: currently the chronicler is asked to narrate
   the *global* picture each turn. A future version could rotate
   per-block focus (US one turn, China the next) for tighter geography.
3. **Multilingual output**: currently PT-BR only; an `--language=en`
   flag would pivot the voice for English-speaking readers without
   changing the engine.
