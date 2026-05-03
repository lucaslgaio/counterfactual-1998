"""Knobs e caps do Modo Jogo.

`CATEGORY_CAPS` define o teto absoluto de magnitude por categoria de ação
classificada pelo GM-LLM. Após o GM retornar JSON, o game_runner CLIPA
qualquer delta que exceda — não rejeita. `clipped` é flagado em ActionResult.

`PARTIAL_FAILURE_SCALE` controla quanto do affected_metrics é aplicado em
caso de partial_failure (side_effects sempre vão integrais).

`TOTAL_FAILURE_COST` é o custo simbólico em lab_funds aplicado em
total_failure (afora qualquer cost que GM tenha retornado).
"""
from __future__ import annotations

from typing import Dict, List


CATEGORY_CAPS: Dict[str, Dict[str, float]] = {
    "research":    {"max_metric_delta": 1.5, "max_metrics_affected": 3},
    "deployment":  {"max_metric_delta": 2.0, "max_metrics_affected": 4},
    "lobby":       {"max_metric_delta": 1.2, "max_metrics_affected": 3},
    "partnership": {"max_metric_delta": 1.5, "max_metrics_affected": 3},
    "comms":       {"max_metric_delta": 1.0, "max_metrics_affected": 4},
    "m_and_a":     {"max_metric_delta": 1.5, "max_metrics_affected": 3},
    # rejected: caps zerados — nada é aplicado
    "rejected":    {"max_metric_delta": 0.0, "max_metrics_affected": 0},
}


# Escala aplicada a affected_metrics quando outcome=partial_failure.
# Side-effects e cost continuam integrais (você pagou o preço, recebeu metade
# do efeito principal).
PARTIAL_FAILURE_SCALE: float = 0.3

# Custo em lab_funds aplicado em total_failure, somado a qualquer cost.lab_funds
# já presente. Negativo = perda. Pequeno mas não zero — falhar tem preço mínimo.
TOTAL_FAILURE_LAB_FUNDS: float = -0.02


# Métricas válidas — chave do metric_taxonomy. Para vetorizadas, listamos
# também as chaves com sufixo de bloco. Para matriz, listamos com sufixo de par.
# (Carregado dinamicamente a partir do spec; este é só fallback de docs.)
def list_available_metrics() -> List[str]:
    """Carrega chaves válidas do metric_taxonomy.json em runtime.

    Inclui chaves vetorizadas com sufixo .US/.EU/.CN/.RoW e matriz com
    pares (US_CN, etc) — formato exato que o motor aceita em
    user_input_deltas.
    """
    import json
    from pathlib import Path

    from src.engine.state import BLOCKS

    spec_path = Path(__file__).parent.parent.parent / "spec" / "metric_taxonomy.json"
    tax = json.loads(spec_path.read_text(encoding="utf-8"))
    out: List[str] = []
    for m in tax["metrics"]:
        key = m["metric_key"]
        cat = m["category"]
        if cat == "global":
            out.append(key)
        elif cat == "vectorized":
            for b in BLOCKS:
                out.append(f"{key}.{b}")
            out.append(key)  # também sem sufixo (motor distribui)
        elif cat == "matrix":
            for pair in (m.get("initial_values") or {}).keys():
                out.append(f"{key}.{pair}")
            out.append(key)
    return sorted(set(out))
