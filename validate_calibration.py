#!/usr/bin/env python3
"""
Validação de calibração do Modo Jogo — Counterfactual-1998.

Roda 3 estratégias contrastantes contra a API local e tabula resultados.
Pré-requisito: `uvicorn src.api.main:app --port 8000` rodando em outro terminal.

Não usa GM-LLM (só ações canônicas) — valida balanceamento mecânico, não interpretação.
"""

import requests
from dataclasses import dataclass
from typing import List, Dict, Any

API = "http://localhost:8000"
SEED = 42
MISSION = "agi_aligned"


@dataclass
class Strategy:
    name: str
    actions: List[str]
    expectation: str  # "win" | "lose" | "uncertain"


STRATEGIES = [
    Strategy(
        name="conservador",
        # Custo total: -0.86 (cabe no orçamento inicial de 1.0). Precisa de
        # 10 ações pra missão poder avaliar win conditions com at_turn=10;
        # versão anterior com 9 ações terminava no turn 9 ainda in_progress.
        actions=[
            "invest_alignment", "invest_alignment",
            "publish_open", "publish_open", "publish_open",
            "push_capability", "push_capability", "push_capability", "push_capability", "push_capability",
        ],
        expectation="win",
    ),
    Strategy(
        name="balanceado",
        actions=[
            "push_capability", "push_capability",
            "invest_alignment", "invest_alignment",
            "deploy_commercial", "deploy_commercial",
            "publish_open", "publish_open",
            "government_partnership", "government_partnership",
        ],
        expectation="uncertain",
    ),
    Strategy(
        name="suicida",
        actions=[
            "rush_to_market", "rush_to_market", "rush_to_market",
            "hide_capabilities", "hide_capabilities", "hide_capabilities",
            "push_capability", "push_capability",
            "aggressive_hiring", "aggressive_hiring",
        ],
        expectation="lose_early",  # turn <= 5
    ),
    Strategy(
        name="all_in_capability",
        actions=[
            "push_capability", "push_capability", "push_capability",
            "deploy_commercial", "deploy_commercial", "deploy_commercial",
            "aggressive_hiring", "aggressive_hiring",
            "rush_to_market", "rush_to_market",
        ],
        expectation="lose",
    ),
]


def run_strategy(strategy: Strategy) -> Dict[str, Any]:
    r = requests.post(f"{API}/game", json={"seed": SEED, "mission_id": MISSION})
    r.raise_for_status()
    game_id = r.json()["game_id"]

    log = []
    final_status = "unknown"
    final_turn = 0

    for i, action_id in enumerate(strategy.actions, start=1):
        r = requests.post(
            f"{API}/game/{game_id}/action",
            json={"type": "canonical", "action_id": action_id},
        )
        r.raise_for_status()
        data = r.json()
        state = data["state"]
        status = state["status"]
        turn = state["current_turn"]
        ps = state["player_state"]

        log.append({
            "turn": turn,
            "action": action_id,
            "lab_funds": round(ps["lab_funds"], 3),
            "accident_risk": round(ps["accident_risk"], 3),
            "exposure_risk": round(ps["exposure_risk"], 3),
            "lab_lead": round(ps["lab_lead_over_rivals"], 2),
            "reputation": round(ps["reputation"], 3),
            "status": status,
            "risk_events": data["action_result"].get("risk_events", []),
        })

        if status != "in_progress":
            final_status = status
            final_turn = turn
            break
    else:
        final_status = state["status"]
        final_turn = state["current_turn"]

    return {
        "name": strategy.name,
        "expectation": strategy.expectation,
        "actual": final_status,
        "ended_at_turn": final_turn,
        "log": log,
    }


def evaluate(result: Dict[str, Any]) -> str:
    name = result["name"]
    exp = result["expectation"]
    act = result["actual"]
    turn = result["ended_at_turn"]

    if exp == "win" and act == "won":
        return "OK"
    if exp == "win" and act == "lost":
        return "TOO_LETHAL — conservador morreu, reduzir PASSIVE_RISK"
    if exp == "lose_early" and act == "lost" and turn <= 5:
        return "OK"
    if exp == "lose_early" and act == "lost" and turn > 5:
        return "ALMOST — suicida morreu mas tarde demais"
    if exp == "lose_early" and act == "won":
        return "BROKEN — suicida venceu, aumentar accident_risk de rush+hide"
    if exp == "lose" and act == "lost":
        return "OK"
    if exp == "lose" and act == "won":
        return "TOO_FORGIVING — all_in_capability venceu, aumentar passive_risk"
    if exp == "uncertain":
        return f"INFO — balanceado: {act} no turno {turn}"
    return f"UNKNOWN — exp={exp}, act={act}, turn={turn}"


def main():
    print(f"Validação de calibração — seed={SEED}, mission={MISSION}\n")
    print(f"{'estratégia':<20} {'esperado':<14} {'atual':<10} {'turno':<6} avaliação")
    print("-" * 90)

    results = []
    for strategy in STRATEGIES:
        try:
            result = run_strategy(strategy)
            verdict = evaluate(result)
            results.append((result, verdict))
            print(
                f"{result['name']:<20} {result['expectation']:<14} "
                f"{result['actual']:<10} {result['ended_at_turn']:<6} {verdict}"
            )
        except Exception as e:
            print(f"{strategy.name:<20} ERROR: {e}")

    print("\n" + "=" * 90)
    print("DETALHE DO BALANCEADO (estratégia mais informativa):")
    print("=" * 90)
    for r, _ in results:
        if r["name"] == "balanceado":
            for entry in r["log"]:
                events_str = f" {entry['risk_events']}" if entry["risk_events"] else ""
                print(
                    f"  T{entry['turn']:<2} {entry['action']:<24} "
                    f"funds={entry['lab_funds']:<6} "
                    f"acc_risk={entry['accident_risk']:<6} "
                    f"exp_risk={entry['exposure_risk']:<6} "
                    f"lead={entry['lab_lead']:<7} "
                    f"rep={entry['reputation']:<7} "
                    f"[{entry['status']}]{events_str}"
                )

    print("\nCole este output todo (tabela + detalhe do balanceado) na próxima mensagem do chat.")


if __name__ == "__main__":
    main()
