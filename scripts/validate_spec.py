# DRAFT - revisar com humano
"""Run the full spec validator and print a markdown report.

Usage:
    python scripts/validate_spec.py

Exit code:
    0 if all checks pass
    1 if any errors are reported
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.spec.validation import run_full_validation


def main() -> int:
    report = run_full_validation()
    print("# Spec validation report\n")
    print("## Stats\n")
    for key, val in report.stats.items():
        print(f"- **{key}**: {val}")
    print()

    if report.warnings:
        print("## Warnings\n")
        for w in report.warnings:
            print(f"- {w}")
        print()

    if report.errors:
        print("## Errors\n")
        for e in report.errors:
            print(f"- {e}")
        print()
        print(f"\n**FAILED** with {len(report.errors)} error(s).")
        return 1

    print("## Result\n")
    print("**OK** — all spec files passed validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
