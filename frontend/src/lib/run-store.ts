import { create } from "zustand";
import {
  LOADED_RUNS,
  LOADED_TURNS_BY_RUN,
  ACTIVE_SOURCE,
  REAL_RUN_COUNT,
  TOTAL_TURNS,
  MOCK_TURN_LABELS,
  getDataSource,
} from "./real-data-loader";
import { MOCK_TURNS } from "./mock-data";
import type { RunConfig, Turn } from "./types";

interface RunState {
  runs: RunConfig[];
  turnsByRun: Record<string, Turn[]>;
  currentTurnIndex: Record<string, number>;
  isAdvancing: boolean;

  getRun: (id: string) => RunConfig | undefined;
  getTurns: (id: string) => Turn[];
  getCurrentTurn: (id: string) => Turn | undefined;

  advanceTurn: (runId: string) => void;
  goToTurn: (runId: string, idx: number) => void;
  setAdvancing: (b: boolean) => void;
  createRun: (cfg: Omit<RunConfig, "id" | "createdAt" | "currentTurn">) => RunConfig;
}

export const useRunStore = create<RunState>((set, get) => ({
  runs: LOADED_RUNS,
  turnsByRun: LOADED_TURNS_BY_RUN,
  currentTurnIndex: Object.fromEntries(LOADED_RUNS.map(r => [r.id, r.currentTurn])),
  isAdvancing: false,

  getRun: (id) => get().runs.find(r => r.id === id),
  getTurns: (id) => get().turnsByRun[id] ?? [],
  getCurrentTurn: (id) => {
    const turns = get().turnsByRun[id] ?? [];
    const idx = get().currentTurnIndex[id] ?? 0;
    return turns[idx];
  },

  advanceTurn: (runId) => {
    const cur = get().currentTurnIndex[runId] ?? 0;
    const turns = get().turnsByRun[runId] ?? [];
    const next = Math.min(cur + 1, turns.length - 1);
    set(state => ({ currentTurnIndex: { ...state.currentTurnIndex, [runId]: next } }));
  },
  goToTurn: (runId, idx) => {
    set(state => ({ currentTurnIndex: { ...state.currentTurnIndex, [runId]: idx } }));
  },
  setAdvancing: (b) => set({ isAdvancing: b }),
  createRun: (cfg) => {
    // New runs created interactively are always mock-backed for now —
    // the Python engine produces JSONs out-of-band, not in response to UI.
    const id = "run_" + Math.random().toString(36).slice(2, 8);
    const run: RunConfig = { ...cfg, id, createdAt: new Date().toISOString(), currentTurn: 0 };
    set(state => ({
      runs: [run, ...state.runs],
      turnsByRun: { ...state.turnsByRun, [id]: MOCK_TURNS },
      currentTurnIndex: { ...state.currentTurnIndex, [id]: 0 },
    }));
    return run;
  },
}));

export { TOTAL_TURNS, MOCK_TURN_LABELS, ACTIVE_SOURCE, REAL_RUN_COUNT, getDataSource };
