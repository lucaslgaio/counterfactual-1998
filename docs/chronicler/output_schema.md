# Chronicler output schema

The chronicler returns a `ChroniclerOutput` per turn. JSON shape:

```json
{
  "narrative": "<150-300 word PT-BR prose, single paragraph or two>",
  "key_developments": [
    "Short bullet 1",
    "Short bullet 2",
    "..."
  ],
  "event_outcome_explanation": "<prose, or null>",
  "confidence": "low" | "medium" | "high",
  "metadata": {
    "lens": "<sociological lens for this turn>",
    "seeds_count": 4,
    "latency_seconds": 4.2,
    "model": "gemini-2.5-flash",
    "temperature": 0.85,
    "prompt_tokens": 1024,
    "completion_tokens": 487,
    "total_tokens": 1511,
    "word_count": 213,
    "word_count_warning": false
  }
}
```

## Field-by-field contract

### `narrative` (string, required)

Continuous prose in PT-BR, 150-300 words. Describes the turn from a
sociological angle, anchored to the lens for this turn (in `metadata.lens`).
Names specific actors, organizations, places. Does not invent numbers.

If the chronicler returns < 150 or > 300 words, the parser logs a
`word_count_warning` in metadata but does not fail (set
`strict_word_count=True` to fail-fast).

### `key_developments` (list of strings, required)

3-6 short headlines (5-12 words each) summarizing the turn's salient
points. Used by the Lovable frontend as a "what happened this turn" bar.

### `event_outcome_explanation` (string or null)

Required when the engine sampled an event for this turn (i.e.
`turn_result.sampled_event != None`). Contains a short PT-BR prose
explanation of *why* the specific variant was sampled — mentioning
modulators (composite_factors) and current state.

`null` when the engine didn't sample an event (most turns).

### `confidence` (enum, required)

`"low"` | `"medium"` | `"high"`. The chronicler's *subjective* judgement
about how coherent the turn is. NOT a rating of the engine's numerical
quality — it's a self-assessment of the prose.

A `"low"` rating typically means the chronicler couldn't reconcile the
deltas with the lens and seeds. The frontend can flag these turns for
user review.

### `metadata` (dict, optional)

Diagnostic information attached by the chronicler infrastructure:
- `lens`: which of the 10 sociological lenses was used
- `seeds_count`: how many discourse seeds went into the prompt (usually 4)
- `latency_seconds`: round-trip latency of the Gemini call
- `model`, `temperature`: API call parameters
- `prompt_tokens`, `completion_tokens`, `total_tokens`: usage from API
- `word_count`: actual word count of `narrative`
- `word_count_warning`: True if outside the 150-300 range

## Compatibility with the Lovable frontend mock

The Lovable mock that the team uses today emits roughly this same shape:

```js
{
  narrative: "...",
  key_developments: [...],
  confidence: "...",
  // some additional motor fields the mock generates locally
}
```

To bridge: the frontend should consume `chronicler_output` as the prose
half and `turn_result` as the structured half. The combined object emitted
by `scripts/run_simulation_with_chronicler.py` already lays them side-by-side.

## What's NOT in the chronicler output

These are owned by the engine (`turn_result` half) and the chronicler
must not duplicate them:

- `deltas` (global, block, matrix)
- `causal_links_active`
- `sampled_event` (the chronicler explains it; the engine emits it)
- `sampled_shock`
- `state_before` / `state_after`

If a future Lovable feature needs aggregated "narrative + numbers" rows,
the consumer joins `turn_result.global_deltas` with
`chronicler_output.narrative` at render time. The two layers are kept
separate at the data level intentionally — it makes A/B testing the
chronicler against alternative narrative engines trivial.

## Validation

Output is validated by `src/chronicler/output_parser.py`. A malformed
response triggers `MalformedResponseError` which the retry layer treats
as transient (lowers temperature on next attempt). Three malformed
attempts in a row escalate to the caller.

Default validation:
- All required fields present
- `narrative` non-empty
- `key_developments`: 3-6 items
- `confidence` ∈ {low, medium, high}
- `event_outcome_explanation` present iff engine sampled an event
- Word count: 150-300 (warning, not error, by default)

Strict word-count validation can be toggled by passing
`strict_word_count=True` to `parse_chronicler_response`.
