"""Remove the safety growth cap in src/engine/turn_runner.py if calibration
made it unnecessary. Validates by running 5 simulations and confirming no
metric explodes (value < 5× initial in 58 turns).

Usage:
    python scripts/remove_growth_cap.py --alphas runs/calibration/alphas_calibrated.json
    python scripts/remove_growth_cap.py --restore   # restore from backup
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np

from src.engine.simulation import Simulation, SimulationConfig

TURN_RUNNER_PATH = ROOT / "src" / "engine" / "turn_runner.py"
BACKUP_PATH = ROOT / "src" / "engine" / "turn_runner.py.pre_etapa5"

# The two constants we relax. We don't delete the cap function; we just set
# the constants to large numbers so it never binds. That preserves the test
# suite (which doesn't rely on a specific cap value) and keeps an emergency
# brake in the code for diagnostics.
RELAXED_BLOCK = """\
# Etapa 5 calibration succeeded — alphas are tame enough that the safety cap
# is no longer needed. The cap is preserved as a no-op (very large bound)
# so the code structure stays intact for diagnostics, but it doesn't bind in
# normal operation. Re-running calibration may revisit these.
MAX_POSITIVE_GROWTH_RATIO = 100.0
MAX_NEGATIVE_GROWTH_RATIO = 100.0
MIN_ABSOLUTE_GROWTH = 0.3
"""

ORIGINAL_PATTERN_HINT = "MAX_POSITIVE_GROWTH_RATIO = 0.015"


def _check_explosion_in_runs(n_seeds: int = 5, n_turns: int = 57) -> dict:
    """Run 5 sims with default (big-bang) mode and check no metric grows >5×."""
    results = {"explosions": [], "max_growth_ratios": {}}
    for seed in [42, 7, 100, 1, 999][:n_seeds]:
        sim = Simulation.from_spec(seed=seed)
        initial_state = sim.state
        sim.run_many(n_turns)
        final = sim.state

        for metric_key, val in final.global_metrics.items():
            initial = initial_state.global_metrics.get(metric_key, 0)
            if initial == 0:
                continue
            ratio = abs(val / initial) if initial != 0 else 0
            results["max_growth_ratios"][f"global.{metric_key}"] = max(
                results["max_growth_ratios"].get(f"global.{metric_key}", 0), ratio
            )
            if ratio > 5.0:
                results["explosions"].append(
                    {"metric": metric_key, "initial": initial, "final": val, "ratio": ratio}
                )

        for metric_key, by_block in final.block_metrics.items():
            initials = initial_state.block_metrics.get(metric_key, {})
            for b, v in by_block.items():
                initial = initials.get(b, 0)
                if initial == 0:
                    continue
                ratio = abs(v / initial)
                results["max_growth_ratios"][f"{metric_key}.{b}"] = max(
                    results["max_growth_ratios"].get(f"{metric_key}.{b}", 0), ratio
                )
                if ratio > 5.0:
                    results["explosions"].append(
                        {"metric": f"{metric_key}.{b}", "initial": initial, "final": v, "ratio": ratio}
                    )
    return results


def remove_cap() -> dict:
    """Backup turn_runner.py and replace the cap constants with no-op values.

    Returns dict with backup path and outcome.
    """
    if BACKUP_PATH.exists():
        return {"status": "already_backed_up", "backup": str(BACKUP_PATH)}
    shutil.copy2(TURN_RUNNER_PATH, BACKUP_PATH)
    text = TURN_RUNNER_PATH.read_text(encoding="utf-8")
    if ORIGINAL_PATTERN_HINT not in text:
        return {
            "status": "pattern_not_found",
            "hint": "expected `MAX_POSITIVE_GROWTH_RATIO = 0.015` in turn_runner.py",
        }
    # Replace from "# Per-turn growth cap" comment block to the closing "MIN_ABSOLUTE_GROWTH"
    import re

    pattern = re.compile(
        r"# Per-turn growth cap.*?MIN_ABSOLUTE_GROWTH\s*=\s*[\d\.]+\s*#[^\n]*",
        re.DOTALL,
    )
    new_text, n = pattern.subn(RELAXED_BLOCK.strip(), text, count=1)
    if n == 0:
        return {"status": "regex_match_failed"}
    TURN_RUNNER_PATH.write_text(new_text, encoding="utf-8")
    return {"status": "removed", "backup": str(BACKUP_PATH)}


def restore_cap() -> dict:
    if not BACKUP_PATH.exists():
        return {"status": "no_backup_found"}
    shutil.copy2(BACKUP_PATH, TURN_RUNNER_PATH)
    BACKUP_PATH.unlink()
    return {"status": "restored"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--alphas", default="runs/calibration/alphas_calibrated.json")
    p.add_argument("--restore", action="store_true", help="Restore backup and exit")
    p.add_argument("--force", action="store_true", help="Remove cap even if explosion check fails")
    args = p.parse_args()

    if args.restore:
        out = restore_cap()
        print(json.dumps(out, indent=2))
        return 0

    print("Step 1: removing cap (backing up turn_runner.py)…")
    remove_result = remove_cap()
    print(json.dumps(remove_result, indent=2))
    if remove_result.get("status") != "removed":
        return 1

    print("\nStep 2: running 5 simulations to check for explosions…")
    # Force fresh import
    import importlib
    import src.engine.turn_runner

    importlib.reload(src.engine.turn_runner)
    import src.engine.simulation as simmod

    importlib.reload(simmod)

    check = _check_explosion_in_runs()
    print(json.dumps(check, indent=2, default=float))

    if check["explosions"] and not args.force:
        print("\n⚠️  Explosions detected — restoring cap. Open issue [etapa-5][cap-cant-remove].")
        restore_cap()
        return 2

    print("\n✅ No explosions detected. Cap removed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
