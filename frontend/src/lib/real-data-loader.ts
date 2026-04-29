// Real data loader for Counterfactual-1998.
//
// Tries to load real run JSONs from `public/runs/*.json` (which, in the unified
// monorepo, are populated by `scripts/sync-runs.js` from `../runs/*.json`).
// If no JSONs are found, falls back to the hand-crafted MOCK data.
//
// Public API mirrors what mock-data.ts exposes so the run-store can swap
// between sources transparently.

import type {
  AnchorEvent,
  CausalLink,
  Confidence,
  ExogenousShock,
  GlobalDelta,
  BlockDelta,
  MatrixDelta,
  RunConfig,
  Seed,
  Turn,
  WorldState,
} from "./types";
import {
  MOCK_RUNS,
  MOCK_TURNS,
  MOCK_TURN_LABELS,
  TOTAL_TURNS,
} from "./mock-data";

// ---- Real-run JSON shape (matches Python engine output) -------------------

export interface RealRunJSON {
  metadata: {
    run_id: string;
    seed: number;
    config: {
      name?: string;
      ai_mode?: "big_bang" | "accelerated_curve";
      play_mode?: "manual" | "auto" | "hybrid";
      temperature?: number;
      random_shock_probability?: number;
      model?: "gemini-2.5-flash" | "gemini-2.5-pro";
      notes?: string;
    };
    generated_at: string;
    n_turns: number;
  };
  turns: Array<{
    turn_index: number;
    turn_label: string;
    state_before: WorldState;
    state_after: WorldState;
    deltas: {
      global: GlobalDelta[];
      block: BlockDelta[];
      matrix: MatrixDelta[];
    };
    event?: AnchorEvent;
    shock?: ExogenousShock;
    causal_links: CausalLink[];
    narrative: string;
    key_developments: string[];
    event_outcome_explanation?: string;
    confidence: Confidence;
    lens: string;
    seeds_used: Seed[];
  }>;
}

// ---- Source tagging -------------------------------------------------------

export type DataSource =
  | { kind: "mock" }
  | { kind: "real"; runId: string; fileName: string };

const SOURCES = new Map<string, DataSource>();

export function getDataSource(runId: string): DataSource {
  return SOURCES.get(runId) ?? { kind: "mock" };
}

// ---- Adapters (snake_case JSON → camelCase domain) ------------------------

function adaptTurn(t: RealRunJSON["turns"][number]): Turn {
  const [yearStr, semStr] = t.turn_label.split("-S");
  const year = Number(yearStr);
  const semester = (Number(semStr) === 2 ? 2 : 1) as 1 | 2;

  return {
    index: t.turn_index,
    label: t.turn_label,
    year,
    semester,
    state: t.state_after,
    prevState: t.state_before,
    event: t.event,
    shock: t.shock,
    narrative: t.narrative,
    keyDevelopments: t.key_developments ?? [],
    deltas: {
      global: t.deltas?.global ?? [],
      block: t.deltas?.block ?? [],
      matrix: t.deltas?.matrix ?? [],
    },
    causalLinks: t.causal_links ?? [],
    lens: t.lens ?? "",
    seeds: t.seeds_used ?? [],
    confidence: t.confidence ?? "medium",
  };
}

function adaptRunConfig(meta: RealRunJSON["metadata"]): RunConfig {
  return {
    id: meta.run_id,
    name: meta.config.name ?? meta.run_id,
    aiMode: meta.config.ai_mode ?? "accelerated_curve",
    playMode: meta.config.play_mode ?? "auto",
    temperature: meta.config.temperature ?? 0.7,
    randomShockProbability: meta.config.random_shock_probability ?? 0.05,
    seed: meta.seed,
    model: meta.config.model ?? "gemini-2.5-flash",
    notes: meta.config.notes,
    createdAt: meta.generated_at,
    currentTurn: 0,
  };
}

// ---- Loader ---------------------------------------------------------------

// Eagerly imports any JSON files placed under `public/runs/`.
// Vite resolves this at build time; in dev it hot-reloads when files change.
const realModules = import.meta.glob("/public/runs/*.json", {
  eager: true,
  import: "default",
}) as Record<string, RealRunJSON>;

interface LoadedData {
  runs: RunConfig[];
  turnsByRun: Record<string, Turn[]>;
  source: "mock" | "real";
  realCount: number;
}

function loadAll(): LoadedData {
  const entries = Object.entries(realModules);

  if (entries.length === 0) {
    // Fallback: mock data
    SOURCES.clear();
    for (const r of MOCK_RUNS) SOURCES.set(r.id, { kind: "mock" });
    return {
      runs: MOCK_RUNS,
      turnsByRun: Object.fromEntries(MOCK_RUNS.map(r => [r.id, MOCK_TURNS])),
      source: "mock",
      realCount: 0,
    };
  }

  const runs: RunConfig[] = [];
  const turnsByRun: Record<string, Turn[]> = {};
  SOURCES.clear();

  for (const [path, json] of entries) {
    try {
      const cfg = adaptRunConfig(json.metadata);
      cfg.currentTurn = Math.max(0, (json.turns?.length ?? 1) - 1);
      const turns = (json.turns ?? []).map(adaptTurn).sort((a, b) => a.index - b.index);
      runs.push(cfg);
      turnsByRun[cfg.id] = turns;
      const fileName = path.split("/").pop() ?? path;
      SOURCES.set(cfg.id, { kind: "real", runId: cfg.id, fileName });
    } catch (err) {
      console.error(`[real-data-loader] failed to parse ${path}:`, err);
    }
  }

  if (runs.length === 0) {
    // Parsing failed for everything → fall back to mock
    for (const r of MOCK_RUNS) SOURCES.set(r.id, { kind: "mock" });
    return {
      runs: MOCK_RUNS,
      turnsByRun: Object.fromEntries(MOCK_RUNS.map(r => [r.id, MOCK_TURNS])),
      source: "mock",
      realCount: 0,
    };
  }

  // Sort: most recent generated_at first
  runs.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1));

  return { runs, turnsByRun, source: "real", realCount: runs.length };
}

const LOADED = loadAll();

export const LOADED_RUNS = LOADED.runs;
export const LOADED_TURNS_BY_RUN = LOADED.turnsByRun;
export const ACTIVE_SOURCE: "mock" | "real" = LOADED.source;
export const REAL_RUN_COUNT = LOADED.realCount;

export { TOTAL_TURNS, MOCK_TURN_LABELS };
