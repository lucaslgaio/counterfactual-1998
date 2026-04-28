# Structural function reference

The engine evaluates each edge in `spec/causal_dag.json` against one of five
parametric forms. The form is declared in `spec/structural_functions.json`.
This document is the canonical reference for what each form does, what
parameters it expects, and when to pick which.

All forms return a **delta** (per-turn change in the target metric, signed).
The engine then applies the delta with a per-turn growth cap (edges only)
and clamps the result to the metric's declared range.

`dt` is implicitly 1.0 — one turn = one semester. Alphas are expressed in
"per-semester" units.

---

## linear

```
delta = alpha · source_value
```

The default form. Used in roughly 70% of the edges. Linear in the source
value, no saturation, no temporal modulation.

| Parameter | Required | Description                                          |
|-----------|----------|------------------------------------------------------|
| `alpha`   | yes      | Coefficient. Negative for inhibitory edges.          |
| `beta`    | no       | Unused for `linear`. Present in spec for symmetry.   |

**When to use**: simple proportional propagation. `e_001` (frontier_capability →
automation_exposure) with `alpha=0.04`: a frontier of 92 contributes
3.68/turn to automation exposure.

**When NOT to use**: when the target should saturate (use `sigmoid`); when
returns diminish (use `log_linear`); when the effect should fade (use
`exponential_decay`).

---

## log_linear

```
delta = alpha · log(1 + source_value / beta)
```

Diminishing returns. Doubling the source produces less than double the
delta. Common for human-capital and education-driven edges.

| Parameter | Required | Description                                                   |
|-----------|----------|---------------------------------------------------------------|
| `alpha`   | yes      | Coefficient.                                                  |
| `beta`    | yes      | Scale parameter. Higher beta → slower onset of saturation.    |

**When to use**: `e_014` (employment_rate → mean_years_schooling) and similar
where each additional unit of input matters less than the previous.

**Care**: pick `beta` of the same order of magnitude as the typical source
value. Setting `beta=1` with a source in 0..100 produces almost-linear
behavior; setting `beta=100` with a source 0..100 keeps you firmly in the
diminishing-returns regime.

---

## sigmoid

```
delta = (target_max − target_value) · σ(alpha · (source − midpoint)) · step_scale
```

Saturating: as `target_value` approaches its ceiling, the delta shrinks
toward zero. Used for adoption-curve-style metrics.

| Parameter      | Required | Description                                                            |
|----------------|----------|------------------------------------------------------------------------|
| `alpha`        | yes      | Steepness of the sigmoid (≈ rate of acceleration around the midpoint). |
| `midpoint`     | no       | Source value at which the inflection happens. Defaults to `beta`.      |
| `beta`         | no       | Alias for `midpoint` (matches the spec's parameter name).              |
| `step_scale`   | no       | Per-turn scale. Default 0.05.                                          |

**When to use**: `e_007` (frontier_capability → population_penetration) with
`beta=95`: frontier accelerates penetration but the contribution shrinks as
penetration approaches 100%.

**Care**: pick `step_scale` low enough that the per-turn delta stays
modest — a high `step_scale` makes the metric jump and the saturation
factor only kicks in after the jump.

---

## exponential_decay

```
delta = alpha · source_value · exp(−elapsed_turns / beta)
```

Effect that fades over time since the source last changed. Used for
edges with a finite "shelf life" — markets pricing AI capability
(`e_004`) is the canonical example: the first surprise is the loudest,
subsequent updates are progressively smaller.

| Parameter | Required | Description                                          |
|-----------|----------|------------------------------------------------------|
| `alpha`   | yes      | Initial coefficient.                                 |
| `beta`    | yes      | Time constant (in turns). Higher beta = slower fade. |

**When to use**: news-driven or attention-driven dynamics. Anything with a
"shock and adapt" pattern.

**Care**: in MVP we use `elapsed_turns = max(1, edge.lag_turns)` as a proxy
for "turns since the source changed". This will be refined in Etapa 5 with
proper history tracking.

---

## sigmoid_temporal

```
delta = alpha_pre · source_value           if  activation_value < threshold
delta = alpha_post · source_value          if  activation_value ≥ threshold
```

A two-regime linear function whose magnitude switches when an external
"activation" metric crosses a threshold. Captures dose-response shifts
that happened historically and aren't well-modeled by a single alpha.

| Parameter            | Required | Description                                                                   |
|----------------------|----------|-------------------------------------------------------------------------------|
| `alpha_pre`          | yes      | Coefficient before threshold crossed.                                         |
| `alpha_post`         | yes      | Coefficient after threshold crossed.                                          |
| `activation_metric`  | yes      | Metric whose value gates the regime switch (e.g. `ai_capability.population_penetration`). |
| `activation_block`   | yes      | `weighted_mean` / `leader` / `US` / `EU` / etc. — how to reduce a vectorized activation_metric to a scalar. |
| `threshold`          | yes      | Numeric threshold for the activation_metric.                                  |

**When to use**: only when there's a clear historical kink. `e_024`
(disinformation → democracy) uses this to model the post-2016 Brexit/
Trump moment when disinformation's bite intensified — `alpha_pre = -0.02`,
`alpha_post = -0.08`.

**Care**: the activation_metric has to be resolvable in the current
WorldState. Don't reference forward-defined composites or matrix metrics
without checking that the resolver can find them.

---

## Self-loop saturation

Any edge with `is_self_loop=true` (e.g. `e_131` publications, `e_121`
democracy, `e_074` penetration) gets an additional **multiplicative
saturation factor** on top of whatever form it uses:

```
delta_saturated = delta · max(0, 1 − (target_value − target_min) / (target_max − target_min))
```

This factor is 1 at the lower bound, 0 at the upper bound. It ensures
that no positive feedback loop can drive a metric past its ceiling — the
critical invariant tested by `test_self_loop_saturation_prevents_explosion`.

If the target has no declared range (rare), a soft cap of 5%/turn growth
is applied instead.

Negative deltas on self-loops are **not** saturated — decay flows freely.

---

## The magnitude → alpha default

When a function in `spec/structural_functions.json` doesn't specify
`alpha`, the engine falls back to a magnitude-based default:

| Magnitude    | Alpha |
|--------------|-------|
| `negligible` | 0.02  |
| `weak`       | 0.10  |
| `medium`     | 0.30  |
| `strong`     | 0.70  |

These will be revised in Etapa 5 calibration. They live in
`src/engine/functions.py::DEFAULT_MAGNITUDE_ALPHA`.

---

## Direction sign-flipping

Edges with `direction: "negative"` have any positive alpha automatically
flipped to its negative. So `e_002` (population_penetration →
employment_rate) with `alpha = 0.02` and `direction = "negative"`
effectively uses `alpha = -0.02`.
