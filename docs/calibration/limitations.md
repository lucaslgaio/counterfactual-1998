# Calibration limitations

## Data sourcing

**7 of ~13 anticipated historical series have data.** The rest are
PLACEHOLDER files marking what's needed:

- Per-bloc series (Gini, mean_years_schooling, V-Dem) require downloading
  primary CSVs from WID/UNDP/V-Dem and aggregating to the 4-bloc taxonomy.
- This is mechanical work but cumulative — each series adds 5–15 minutes
  of careful aggregation.

The 7 series we have are **approximated from public summary statistics**
rather than primary CSV downloads. Confidence values (0.6–0.8) reflect
this. A direct re-fetch from primary sources would push confidence to
0.9+ and likely tighten the per-series MAEs.

## Frequency conversion

All series are stored at semestral resolution to align with the engine's
turn cadence. Annual data is **linearly interpolated** between known
annual points, which is an approximation:

- For monotone metrics (life expectancy, top1pct_share), interpolation
  is ~harmless.
- For metrics with intra-year volatility (financial_markets.global_index
  has 6-month swings during crises), interpolation undersmooths and may
  produce per-turn errors that look worse than they are. The headline
  fit (MAE_norm 0.013) is fine, but turn-by-turn comparisons would
  reveal the smoothing.

## Coverage of the parameter space

Calibration only optimizes alphas/betas of edges whose **targets have
historical data**. Of the spec's ~130 edges, only 19 parameters made it
into the fit (Tarefa 11 in the etapa-5 spec expected ~30–50). The
narrower parameter space is a direct consequence of the 7-series cap.

Edges whose targets are still uncovered:
- `science_rd.publications_index` (and breakthroughs_per_year)
- `inequality.gini_intra_block` per bloc
- `health.mental_wellbeing` per bloc
- `governance.democracy_index` per bloc (and ai_regulation_maturity)
- `tech_industry.bigtech_concentration` per bloc
- `labor_market.automation_exposure`
- `information_ecosystem.disinformation_level` (and media_trust)
- `health.diagnostic_accuracy`
- `education.cost_index`

These edges retain the spec's draft alphas. The Etapa-4 growth cap
remains the bound that keeps them from saturating in 58 turns.

## Optimizer

L-BFGS-B converged in 30 iterations to a local minimum. Without
differential evolution as a sanity check, we can't rule out that a
better minimum exists. With more parameters and more data, future
calibrations should run DE for at least one pass.

## Cap removal blocked

See [issue #13](../../issues). The cap can't be safely removed until
calibration covers the explosive edges. The cap is a known leakage path
between Etapa 4 and Etapa 5 — its presence means the engine's
trajectories are still mildly attenuated by the cap rather than purely
driven by calibrated parameters.

## What this means for paper claims

Acceptable claims (with the current calibration):
- "The 7 most important global aggregates fit within MAE_norm 0.07 on
  average for the null treatment."
- "When we switch to big-bang mode, the difference in those 7 series is
  the AI-shock effect."
- "0 critical-sensitivity parameters: the fit is robust to ±20% perturbations."

Claims that need more data first:
- "All metrics are calibrated against historical reality." (Only 7 are.)
- "The engine reproduces 1998–2024 with no remaining tuning knobs."
  (The growth cap is still in play for ~50 edges.)
- "Per-block trajectories are validated." (We only have global aggregates.)

## What to do next

1. **Source 3-5 PLACEHOLDER series.** Highest-leverage: per-bloc Gini,
   per-bloc mean_years_schooling, per-bloc V-Dem. Each unlocks 4–10
   additional alphas to calibrate.
2. **Re-run `scripts/calibrate.py`** — pipeline auto-discovers new CSVs.
3. **Re-attempt cap removal** with the wider calibration.
4. **If still blocked**, manually constrain the spec's draft alphas for
   the explosive edges (e_037, e_131, e_028) using the magnitude-default
   table from the etapa-4 spec — this is judgement-based but bounded.
