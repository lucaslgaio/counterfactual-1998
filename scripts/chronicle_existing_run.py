"""Chronicle a previously-saved engine run.

Useful when you've run scripts/run_simulation.py earlier and want to add
narrative on top without re-running the engine.

Usage:
    python scripts/chronicle_existing_run.py \
        --motor-output runs/run_001.json \
        --output runs/run_001_chronicled.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.chronicler.chronicler import ChroniclerSession
from src.chronicler.gemini_client import GeminiClient
from src.engine.delta_computer import CausalLinkActive, DeltaPackage
from src.engine.event_sampler import SampledEvent
from src.engine.shock_sampler import SampledShock
from src.engine.state import WorldState
from src.engine.turn_runner import TurnResult


def _rebuild_event(d: dict) -> SampledEvent:
    return SampledEvent(
        event_id=d["event_id"],
        turn_label=d["turn_label"],
        variant_id=d["variant_id"],
        description=d["description"],
        delta_package_id=d["delta_package_id"],
        base_probability=d["base_probability"],
        effective_probability=d["effective_probability"],
        modulator_log=dict(d.get("modulator_log", {})),
        provenance=dict(d.get("provenance", {})),
    )


def _rebuild_shock(d: dict) -> SampledShock:
    return SampledShock(
        shock_id=d["shock_id"],
        description=d["description"],
        delta_package=dict(d.get("delta_package", {})),
        provenance=dict(d.get("provenance", {})),
    )


def _rebuild_delta_package(d: dict) -> DeltaPackage:
    pkg = DeltaPackage()
    pkg.edge_global_deltas = dict(d.get("edge_global_deltas", {}))
    pkg.edge_block_deltas = {
        k: dict(v) for k, v in d.get("edge_block_deltas", {}).items()
    }
    pkg.edge_matrix_deltas = {
        k: dict(v) for k, v in d.get("edge_matrix_deltas", {}).items()
    }
    pkg.exogenous_global_deltas = dict(d.get("exogenous_global_deltas", {}))
    pkg.exogenous_block_deltas = {
        k: dict(v) for k, v in d.get("exogenous_block_deltas", {}).items()
    }
    pkg.exogenous_matrix_deltas = {
        k: dict(v) for k, v in d.get("exogenous_matrix_deltas", {}).items()
    }
    pkg.causal_links_active = [
        CausalLinkActive(
            edge_id=link["edge_id"],
            source=link["source"],
            target=link["target"],
            source_value=link["source_value"],
            contribution=link["contribution"],
            form=link["form"],
        )
        for link in d.get("causal_links_active", [])
    ]
    pkg.provenance = dict(d.get("provenance", {}))
    return pkg


def _rebuild_turn_result(turn_data: dict) -> TurnResult:
    state_before = WorldState.from_json(turn_data["state_before"])
    state_after = WorldState.from_json(turn_data["state_after"])
    sampled_event = (
        _rebuild_event(turn_data["sampled_event"]) if turn_data.get("sampled_event") else None
    )
    sampled_shock = (
        _rebuild_shock(turn_data["sampled_shock"]) if turn_data.get("sampled_shock") else None
    )
    return TurnResult(
        turn_index=turn_data["turn_index"],
        turn_label=turn_data["turn_label"],
        state_before=state_before,
        state_after=state_after,
        delta_package=_rebuild_delta_package(turn_data["delta_package"]),
        sampled_event=sampled_event,
        sampled_shock=sampled_shock,
        user_input_deltas=dict(turn_data.get("user_input_deltas", {})),
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--motor-output", type=str, required=True)
    p.add_argument("--output", type=str, required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--model", type=str, default="gemini-2.5-flash")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    if not args.quiet:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    data = json.loads(Path(args.motor_output).read_text(encoding="utf-8"))
    history = data.get("history", [])
    if not history:
        print("ERROR: motor-output has no 'history' field; nothing to chronicle.")
        return 1

    if not args.quiet:
        print(f"Loaded {len(history)} turns from {args.motor_output}")

    turn_results = [_rebuild_turn_result(t) for t in history]
    states = [turn_results[0].state_before] + [r.state_after for r in turn_results]

    client = GeminiClient.from_env(model=args.model)
    session = ChroniclerSession(client=client, seed=args.seed)

    if not args.quiet:
        print(f"Chronicling via {args.model}…")
    t0 = time.time()
    chronicled = []
    for i, r in enumerate(turn_results):
        out = session.chronicle_turn(r, states[i], states[i + 1])
        chronicled.append(out)
        if not args.quiet and (i + 1) % 5 == 0:
            print(f"  {i + 1}/{len(turn_results)} turns chronicled")
    elapsed = time.time() - t0

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined = {
        "source_motor_output": str(args.motor_output),
        "chronicler_runtime_seconds": elapsed,
        "config": data.get("config", {}),
        "current_state": data.get("current_state", {}),
        "turns": [
            {"turn_result": h, "chronicler_output": c.to_json()}
            for h, c in zip(history, chronicled)
        ],
    }
    out_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.quiet:
        print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes) in {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
