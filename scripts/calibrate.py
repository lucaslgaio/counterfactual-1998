"""Run end-to-end calibration and persist artifacts.

Usage:
    python scripts/calibrate.py \
        --output-dir runs/calibration/ \
        --n-runs-per-eval 3 \
        --max-iterations 60 \
        --use-de
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.calibration.runner import CalibrationConfig, run_full_calibration


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=str, default="runs/calibration/")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n-runs-per-eval", type=int, default=3)
    p.add_argument("--max-iterations", type=int, default=60, help="L-BFGS max iters")
    p.add_argument("--max-de-iterations", type=int, default=20, help="DE max iters (0 to disable)")
    p.add_argument("--use-de", action="store_true", help="Run differential evolution after L-BFGS")
    p.add_argument("--no-de", dest="use_de", action="store_false")
    p.set_defaults(use_de=False)
    p.add_argument("--regularization-lambda", type=float, default=0.01)
    p.add_argument("--n-turns", type=int, default=57)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if not args.quiet:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    config = CalibrationConfig(
        seed=args.seed,
        n_runs_per_eval=args.n_runs_per_eval,
        max_lbfgs_iterations=args.max_iterations,
        max_de_iterations=args.max_de_iterations,
        use_de=args.use_de,
        regularization_lambda=args.regularization_lambda,
        n_turns=args.n_turns,
    )

    summary = run_full_calibration(
        output_dir=Path(args.output_dir),
        config=config,
    )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
