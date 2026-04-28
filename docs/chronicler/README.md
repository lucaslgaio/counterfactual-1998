# Chronicler — LLM narrative layer (Etapa 6)

The chronicler turns the SDM engine's structured output into prose. It is
**read-only** with respect to the engine: it never invents numbers, causal
links, or events. The engine decides what happens; the chronicler describes
it.

## Quick start

```bash
export GEMINI_API_KEY="…"   # or GOOGLE_API_KEY (legacy)
python scripts/run_simulation_with_chronicler.py \
    --seed 42 --turns 58 --output runs/full_run.json
```

Output is a single JSON containing both layers per turn:

```json
{
  "turns": [
    {
      "turn_result": { /* TurnResult from src.engine */ },
      "chronicler_output": {
        "narrative": "Em outubro de 1999, programadores juniores …",
        "key_developments": [...],
        "event_outcome_explanation": "…",
        "confidence": "medium",
        "metadata": { "lens": "…", "seeds_count": 4, "latency_seconds": 4.2, ... }
      }
    },
    ...
  ]
}
```

The `turn_result` half is byte-identical to what
`scripts/run_simulation.py` would produce alone (the engine is deterministic).
The `chronicler_output` half is non-deterministic prose at the same temperature.

## Module layout

```
src/chronicler/
├── prompts.py           # CHRONICLER_SYSTEM_PROMPT + word-count constants
├── input_builder.py     # builds prompt input from TurnResult + state
├── output_parser.py     # validates Gemini's function_call into ChroniclerOutput
├── discourse.py         # rotates 10 sociological lenses, samples 4 seeds/turn
├── gemini_client.py     # google.genai wrapper, BLOCK_ONLY_HIGH safety, thinking_budget=0
├── retry.py             # typed exceptions + bounded exponential backoff
└── chronicler.py        # ChroniclerSession (public API)
```

## What the chronicler is forbidden to do

The system prompt explicitly bans:
1. Suggesting new `causal_links` (only the engine's are valid)
2. Inventing events not sampled by the engine
3. Inventing or modifying numerical deltas
4. Describing causal mechanisms that contradict engine-identified links
5. Meta-narrative ("the engine got this wrong" — never)

If the chronicler violates these rules, the prompt is wrong; please file
an issue with a transcript.

## Cost

Per 58-turn run with Gemini 2.5 Flash (default):
- ~1k input tokens + ~500 output tokens per call
- 57 calls per run
- At Flash's pricing (~$0.075/1M input, $0.30/1M output as of 2026-04):
  ~57 × ($0.075 × 0.001 + $0.30 × 0.0005) ≈ **$0.013 per run**

A 1000-Monte-Carlo experiment runs ~$13. Cap your runs accordingly.

## Determinism

- Engine: fully deterministic given `seed`.
- Chronicler: lens choice and seed sampling are deterministic given
  `(turn_index, ChroniclerSession.seed)`. The prose itself is non-deterministic
  (temperature 0.85). Two runs with the same seeds will produce different
  prose but the same lens, the same seeds, and very close `confidence` /
  `key_developments` distributions.

## Reproducing the smoke test

After setting `GEMINI_API_KEY`:

```bash
pytest tests/chronicler/test_integration.py -v
```

This runs the engine + chronicler for one and three turns and prints the
narrative. Skipped (with explanation) when the key isn't set.

## Documents in this folder

- `README.md` — this file
- `prompt_design.md` — choices behind the system prompt
- `output_schema.md` — exact structure of `chronicler_output` (consumed by Lovable frontend)
