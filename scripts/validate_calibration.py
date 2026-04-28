"""Re-run null treatment with calibrated alphas and report per-series fit.

Usage:
    python scripts/validate_calibration.py --alphas runs/calibration/alphas_calibrated.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np

from src.calibration.error_metrics import mae_normalized
from src.calibration.historical_loader import load_all_series
from src.calibration.null_treatment import (
    extract_metric_trajectory,
    make_null_treatment_config,
)
from src.calibration.objective import _series_id
from src.calibration.parameter_space import (
    apply_parameters_to_spec,
    build_parameter_space,
)
from src.calibration.runner import _final_run
from src.engine.simulation import build_spec_bundle


def _status_for(mae_norm: float) -> str:
    if mae_norm < 0.05:
        return "EXCELLENT"
    if mae_norm < 0.15:
        return "GOOD"
    if mae_norm < 0.30:
        return "OK"
    return "POOR"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--alphas",
        type=str,
        default="runs/calibration/alphas_calibrated.json",
        help="Path to alphas_calibrated.json from a calibration run",
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n-runs", type=int, default=3)
    p.add_argument("--n-turns", type=int, default=57)
    args = p.parse_args()

    alphas_data = json.loads(Path(args.alphas).read_text(encoding="utf-8"))
    alphas = alphas_data["alphas"]
    print(f"Loaded {len(alphas)} calibrated parameter values from {args.alphas}\n")

    spec = build_spec_bundle()
    historical = load_all_series()
    targets = {s.metric_key for s in historical.values()}
    parameter_space = build_parameter_space(spec, target_metrics_with_data=targets)

    # Reconstruct alpha vector in parameter_space order
    alpha_vector = np.array(
        [alphas.get(p.key, p.initial_value) for p in parameter_space], dtype=float
    )
    new_spec = apply_parameters_to_spec(spec, parameter_space, alpha_vector)

    null_config = make_null_treatment_config(seed=args.seed, n_runs=args.n_runs)
    runs = _final_run(new_spec, null_config, n_turns=args.n_turns)

    print(f"{'Series':<48} {'MAE_norm':>10} {'Status':<12}")
    print("-" * 72)

    rows = []
    for sid, series in sorted(historical.items()):
        pred = extract_metric_trajectory(runs, series.metric_key, series.block)[: len(series.values)]
        rng = spec.metric_ranges.get(series.metric_key, (0.0, 1.0))
        e = mae_normalized(pred, series.values, rng[1] - rng[0])
        if np.isnan(e):
            continue
        status = _status_for(e)
        rows.append((sid, e, status))
        print(f"{sid[:48]:<48} {e:>10.4f} {status:<12}")

    print()
    n = len(rows)
    n_good = sum(1 for _, _, s in rows if s in ("EXCELLENT", "GOOD"))
    n_ok = sum(1 for _, _, s in rows if s == "OK")
    n_poor = sum(1 for _, _, s in rows if s == "POOR")
    print(f"Summary: {n} series total")
    print(f"  EXCELLENT/GOOD (<0.15): {n_good} ({100*n_good/max(1,n):.0f}%)")
    print(f"  OK (0.15-0.30):         {n_ok} ({100*n_ok/max(1,n):.0f}%)")
    print(f"  POOR (>0.30):           {n_poor} ({100*n_poor/max(1,n):.0f}%)")

    target_60 = (n_good + n_ok) >= 0.60 * n
    print(f"  ≥60% under 0.30 (success criterion): {'YES' if target_60 else 'NO'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
