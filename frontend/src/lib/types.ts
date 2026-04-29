// Counterfactual-1998 — domain types
// Reflects new architecture: vectorized state + event variants + chronicler split.

export type BlockId = "US" | "EU" | "CN" | "RoW";
export const BLOCKS: BlockId[] = ["US", "EU", "CN", "RoW"];

export type MetricScope = "global" | "vectorized" | "matrix";

export type GlobalMetricKey =
  | "financial_markets.global_index"
  | "financial_markets.systemic_risk"
  | "education.mean_years_schooling"
  | "education.cost_index"
  | "inequality.global_gini"
  | "inequality.top1pct_share"
  | "health.life_expectancy"
  | "health.diagnostic_accuracy"
  | "science_rd.publications_index"
  | "energy_climate.co2_gt_year"
  | "energy_climate.renewable_share"
  | "information_ecosystem.media_trust";

export type VectorizedMetricKey =
  | "ai_capability.frontier_capability"
  | "ai_capability.population_penetration"
  | "tech_industry.bigtech_concentration"
  | "tech_industry.tech_employment_share"
  | "labor_market.automation_exposure"
  | "labor_market.employment_rate"
  | "governance.democracy_index"
  | "governance.ai_regulation_maturity"
  | "information_ecosystem.disinformation_level"
  | "science_rd.breakthroughs_per_year";

export type MatrixMetricKey =
  | "geopolitics.bilateral_tensions"
  | "geopolitics.active_conflicts";

export type MetricKey = GlobalMetricKey | VectorizedMetricKey | MatrixMetricKey;

export interface MetricMeta {
  key: MetricKey;
  scope: MetricScope;
  domain: string;
  label: string;
  unit: string;
  badWhenUp: boolean;
}

export type GlobalState = Record<GlobalMetricKey, number>;
export type BlockState = Record<VectorizedMetricKey, number>;
export type BlocksState = Record<BlockId, BlockState>;

export interface MatrixState {
  "geopolitics.bilateral_tensions": Record<string, number>; // pair "US_CN"
  "geopolitics.active_conflicts": number;
}

export interface WorldState {
  global: GlobalState;
  blocks: BlocksState;
  matrix: MatrixState;
}

// ---- Events ---------------------------------------------------------------

export type EventStatus = "real" | "altered" | "averted" | "redirected";
export type Severity = "low" | "medium" | "high" | "critical";

export interface EventVariant {
  id: string;
  label: string;
  status: EventStatus;
  description: string;
  baseProbability: number;
  actualProbability: number;
  modulators: { name: string; value: string; effect: number }[];
}

export interface AnchorEvent {
  id: string;
  title: string;
  severity: Severity;
  primaryBlock?: BlockId;
  variant: EventVariant;
}

export interface ExogenousShock {
  id: string;
  title: string;
  description: string;
  primaryBlock?: BlockId;
}

// ---- Causal links ---------------------------------------------------------

export interface CausalLink {
  source: string;
  target: string;
  strength: number;        // 0..1
  polarity: 1 | -1;
  scope: "intra-block" | "spillover" | "global";
}

// ---- Deltas ---------------------------------------------------------------

export interface GlobalDelta {
  key: GlobalMetricKey;
  delta: number;
  why: string;
}

export interface BlockDelta {
  key: VectorizedMetricKey;
  by: Record<BlockId, number>;
  why: string;
}

export interface MatrixDelta {
  key: MatrixMetricKey;
  delta: Record<string, number> | number;
  why: string;
}

// ---- Turn -----------------------------------------------------------------

export type Confidence = "low" | "medium" | "high";

export interface Seed {
  year: number;
  domain: string;
  text: string;
}

export interface Turn {
  index: number;          // 0..57
  label: string;          // "1998-S1"
  year: number;
  semester: 1 | 2;
  state: WorldState;      // state AFTER this turn
  prevState: WorldState;  // state BEFORE this turn
  event?: AnchorEvent;
  shock?: ExogenousShock;
  narrative: string;
  keyDevelopments: string[];
  deltas: {
    global: GlobalDelta[];
    block: BlockDelta[];
    matrix: MatrixDelta[];
  };
  causalLinks: CausalLink[];
  lens: string;
  seeds: Seed[];
  confidence: Confidence;
}

// ---- Run config -----------------------------------------------------------

export interface RunConfig {
  id: string;
  name: string;
  aiMode: "big_bang" | "accelerated_curve";
  playMode: "manual" | "auto" | "hybrid";
  temperature: number;
  randomShockProbability: number;
  seed: number;
  model: "gemini-2.5-flash" | "gemini-2.5-pro";
  notes?: string;
  createdAt: string;
  currentTurn: number;
}
