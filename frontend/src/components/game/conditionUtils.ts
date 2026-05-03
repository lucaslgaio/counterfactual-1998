// Helpers de condition lookup — espelham _evaluate_condition do backend.
import type { Condition, GameState } from "@/types/game";

const BLOCKS = new Set(["US", "EU", "CN", "RoW"]);

export function evalConditionValue(cond: Condition, state: GameState): number | null {
  if (cond.scope === "player") {
    const ps = state.player_state as unknown as Record<string, number>;
    return cond.metric in ps ? ps[cond.metric] : null;
  }
  // engine — chave dot notation pode terminar em .US/.EU/etc ou par US_CN
  const es = state.engine_state;
  if (cond.metric in es.global_metrics) {
    return es.global_metrics[cond.metric];
  }
  // Tenta dividir sufixo
  const parts = cond.metric.split(".");
  if (parts.length >= 2) {
    const last = parts[parts.length - 1];
    const base = parts.slice(0, -1).join(".");
    if (BLOCKS.has(last) && es.block_metrics[base]) {
      const v = es.block_metrics[base][last];
      return v ?? null;
    }
    // Matriz: par US_CN ou "total"
    if (es.matrix_metrics[base]) {
      const v = es.matrix_metrics[base][last];
      return v ?? null;
    }
  }
  return null;
}
