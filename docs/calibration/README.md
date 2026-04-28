# Calibration — Etapa 5

## What's in this folder

- `methodology.md` — null-treatment design, objective function, optimizer choice, sensitivity analysis. Publishable as paper appendix.
- `data_sources.md` — per-series provenance, processing, confidence ratings.
- `results.md` — per-series fit table from the latest calibration run.
- `sensitivity.md` — auto-generated from `runs/calibration/sensitivity_report.json`.
- `limitations.md` — what's missing and why it matters.

## How calibration is wired

```
spec/                        data/historical/
   │                              │
   ▼                              ▼
src/engine/Simulation     src/calibration/historical_loader
   │                              │
   └──────────┬───────────────────┘
              ▼
   src/calibration/objective_function
              ▼
   scipy L-BFGS-B (+ optional DE)
              ▼
   runs/calibration/alphas_calibrated.json
              ▼
   sensitivity analysis + confidence checks
              ▼
   docs/calibration/results.md (this folder)
```

## Reproducing the latest calibration

```bash
python scripts/calibrate.py --output-dir runs/calibration/ \
    --n-runs-per-eval 2 --max-iterations 30 --no-de
python scripts/validate_calibration.py --alphas runs/calibration/alphas_calibrated.json
python scripts/sensitivity_report.py \
    --input runs/calibration/sensitivity_report.json \
    --output docs/calibration/sensitivity.md
```

The deterministic seed makes runs reproducible. With more historical data
in place, run with `--use-de` and `--max-iterations 100` for a deeper
search (still finishes in minutes).

## Status

Calibration succeeded against the 7 historical series available (100% under
MAE_norm 0.15). The growth-cap-removal step did NOT succeed because edges
whose targets lack historical data still rely on uncalibrated draft alphas
— see [issue #13](../../issues) for the path forward.
