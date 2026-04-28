# Calibration methodology

## Null treatment

The simulator runs in two configurations:

- **Big-bang** (default): `ai_capability.frontier_capability` evolves naturally per the DAG. This is the counterfactual — what would happen if a Claude-4-equivalent AI emerged in 1998.
- **Null treatment**: `ai_capability.frontier_capability` is pinned at 15 (pre-1998 ML baseline) for every block at every turn. Other dynamics evolve normally. This represents *our* world.

The null trajectory ought to match historical reality, because in the real
1998–2024 window the AI big-bang did not happen. So **calibration's job is
to find alphas that minimize the gap between the null-treatment trajectory
and historical CSVs**.

Once calibrated, switching to big-bang mode reveals what the AI shock would
have done. The difference between the two trajectories is the project's
research output: per-metric, per-bloc, per-turn.

## Objective function

For an alpha vector `α`:

1. Build a `SpecBundle` with `α` overlaid on the spec's draft alphas.
2. Run `n_runs` null-treatment trajectories, average them per-metric.
3. For each historical series, compute per-metric MAE normalized by
   the metric's range (`MAE_norm = MAE / (range_max - range_min)`).
4. Aggregate: `Σ confidence_w * MAE_norm` weighted by series confidence.
5. Add L1 regularization: `λ * mean(|α - α_initial| / |α_initial|)`,
   penalizing drift away from the spec's draft (which is itself
   literature-anchored).
6. Return the scalar.

Series with all-NaN observations contribute 0 to the aggregate (they
don't pollute the gradient).

## Parameter space

We calibrate `alpha` (and `beta` where applicable) for edges where:

1. Magnitude is `medium` or `strong` (weak edges aren't worth optimizing).
2. The structural form is parametric (`linear`, `log_linear`, `sigmoid`,
   `exponential_decay`, `sigmoid_temporal`).
3. The edge's target metric has a historical CSV (otherwise we can't
   evaluate fit).

Range bounds depend on the edge's `validation_confidence` (Etapa 2):

| Confidence | Range factor | Meaning                                          |
|------------|-------------:|--------------------------------------------------|
| `high`     | ±25%         | Literature constrains this — fine-tune only.     |
| `medium`   | ±60%         | Some flexibility for the data to disagree.       |
| `low`      | ±100%        | Calibration has full say.                        |
| unset      | ±80%         | Default for unvalidated edges.                   |

`high`-confidence edges with positive initial alphas can't go negative
(sign preservation) — and vice versa. This codifies the constraint that
the literature got the *direction* right; calibration just adjusts the
magnitude.

## Optimizer

**L-BFGS-B** (scipy) is the default: deterministic given the starting
point, fast, respects bounds. Limitation: can converge to local minima.

**Differential evolution** (scipy, `--use-de`) is the optional sanity
check: populational, gradient-free, more robust to local minima. We
accept the DE solution only if it improves over L-BFGS by >5%.

For the 7-series, 19-parameter space we currently have, L-BFGS converges
in ~30 iterations (~70s). DE adds ~2 minutes.

## Sensitivity analysis

After calibration, we perturb each parameter ±20% one-at-a-time and
measure the relative change in objective. The dimensionless **elasticity**:

```
elasticity ≈ |∂f/∂α × α / f|
```

- `elasticity > 1.0` → **critical** (small change in α → big change in fit).
  Needs literature backup.
- `0.3 < elasticity ≤ 1.0` → **important**. Worth tracking.
- `elasticity ≤ 0.3` → **robust**. Can trust without fine-grained
  justification.

A high count of `critical` parameters (>10) is a red flag: the model is
fragile and likely needs different functional forms or more data.

## Confidence-constraint validation

After optimization we re-check that no `high`-confidence parameter landed
outside its declared range (a side-effect possible if the optimizer hit a
boundary aggressively, or if numeric issues moved it slightly out of
bounds). Violations are logged as `major` for high-confidence and `minor`
otherwise.

We also count `at_boundary` parameters (within 2% of the range edge) — a
signal that the bound is binding. If many high-confidence edges are at
their boundary, the literature and the data are in tension and the human
needs to decide which to trust.

## Removing the growth cap

The Etapa-4 engine includes a safety cap (`MAX_POSITIVE_GROWTH_RATIO =
0.015`) that prevents edge-derived deltas from compounding into runaway
saturation. The cap is a substitute for proper calibration.

After calibration, we run `scripts/remove_growth_cap.py` which:

1. Backs up `src/engine/turn_runner.py`.
2. Sets the cap constants to large no-op values.
3. Runs 5 seed-varied big-bang simulations.
4. Asserts no metric exceeds 5× initial in 58 turns.
5. If a metric explodes, restores the backup and reports which metrics
   broke and which edges are likely responsible.

For the current Etapa-5 calibration (7 series only), the cap removal
**failed** for metrics whose edges weren't constrained by data — see issue
[#13](../../issues). The cap remains in place until more historical
data is sourced.

## Reproducibility

Every artifact in `runs/calibration/` is derived from:
- The committed spec at the time of run (git SHA).
- The committed historical CSVs.
- The seed (`SimulationConfig.seed`, default 42).

Calling `scripts/calibrate.py` with the same arguments and an unmodified
repo always produces identical numbers. This is non-negotiable for paper
reproducibility.
