"""Generate a markdown sensitivity report from a calibration run.

Usage:
    python scripts/sensitivity_report.py \
        --input runs/calibration/sensitivity_report.json \
        --output docs/calibration/sensitivity.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def _classify_color(c: str) -> str:
    return {
        "critical": "🔴",
        "important": "🟡",
        "robust": "🟢",
    }.get(c, "❔")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="runs/calibration/sensitivity_report.json")
    p.add_argument("--output", default="docs/calibration/sensitivity.md")
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    summary = data["summary"]
    params = data["parameters"]
    params_sorted = sorted(params, key=lambda p: -abs(p["elasticity"]))

    out = []
    out.append("# Calibration sensitivity report")
    out.append("")
    out.append(f"Baseline objective: {data['baseline_objective']:.4f}")
    out.append(f"Perturbation: ±{int(data['perturbation']*100)}%")
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append(f"- 🔴 critical: **{summary['critical']}**")
    out.append(f"- 🟡 important: **{summary['important']}**")
    out.append(f"- 🟢 robust: **{summary['robust']}**")
    out.append("")
    if summary["critical"] >= 10:
        out.append("> ⚠️  Many critical parameters — model is fragile to small perturbations.")
        out.append("> Recommend tightening literature backing for these or considering different functional forms.")
        out.append("")

    out.append("## Detail (sorted by elasticity)")
    out.append("")
    out.append("| | edge_id | parameter | calibrated | elasticity | classification |")
    out.append("|--|---------|-----------|-----------:|-----------:|----------------|")
    for p in params_sorted:
        emoji = _classify_color(p["classification"])
        out.append(
            f"| {emoji} | `{p['edge_id']}` | `{p['parameter_name']}` | "
            f"{p['calibrated_value']:.4f} | {p['elasticity']:.3f} | {p['classification']} |"
        )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(
        f"Critical={summary['critical']}, important={summary['important']}, robust={summary['robust']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
