// Tipos espelham os modelos Pydantic em src/game/models.py.
// Manter em sincronia manualmente — small surface, baixo custo.

export type Scope = "engine" | "player";
export type Operator = ">=" | "<=" | "==" | "!=" | ">" | "<";

export interface Condition {
  metric: string;
  scope: Scope;
  operator: Operator;
  threshold: number;
  at_turn?: number | null;
}

export interface Mission {
  id: string;
  name: string;
  description: string;
  win_conditions: Condition[];
  lose_conditions: Condition[];
}

export interface CanonicalAction {
  id: string;
  label: string;
  prompt_template: string;
  description: string;
  deltas: Record<string, number>;
  cost: Record<string, number>;
}

export type GMClassification =
  | "research" | "deployment" | "lobby"
  | "partnership" | "comms" | "m_and_a" | "rejected";

export interface GMInterpretation {
  classification: GMClassification;
  plausible: boolean;
  affected_metrics: Record<string, number>;
  side_effects: Record<string, number>;
  cost: Record<string, number>;
  success_p: number;
  triggers_accident: boolean;
  narrative_seed: string;
  rejection_reason?: string | null;
}

export type Outcome = "success" | "partial_failure" | "total_failure" | "rejected";

export interface RiskEvent {
  kind: "accident" | "scandal";
  accident_roll?: number | null;
  risk_at_trigger?: number | null;
  narrative_seed: string;
}

export interface ActionResult {
  action_type: "canonical" | "free";
  raw_input: string;
  interpretation?: GMInterpretation | null;
  roll: number;
  outcome: Outcome;
  applied_deltas: Record<string, number>;
  applied_player_deltas: Record<string, number>;
  clipped: boolean;
  clipped_fields: string[];
  risk_events: RiskEvent[];
}

export interface PlayerState {
  lab_funds: number;
  accidents_count: number;
  reputation: number;            // signed [-1, +1]
  accident_risk: number;         // [0, 1]
  exposure_risk: number;         // [0, 1] (transientemente >1 antes do trigger)
  alignment_credit: number;      // >= 0
  lab_lead_over_rivals: number;  // frontier_capability.US − mean(EU,CN,RoW)
}

export interface TurnRecord {
  turn: number;
  turn_label: string;
  year: number;
  action_result: ActionResult;
  engine_delta_summary: Record<string, number>;
  chronicle: string;
}

export interface EngineState {
  turn_index: number;
  turn_label: string;
  global_metrics: Record<string, number>;
  block_metrics: Record<string, Record<string, number>>;
  matrix_metrics: Record<string, Record<string, number>>;
  metadata: Record<string, unknown>;
}

export interface GameState {
  game_id: string;
  seed: number;
  mission: Mission;
  current_turn: number;
  engine_state: EngineState;
  player_state: PlayerState;
  history: TurnRecord[];
  status: "in_progress" | "won" | "lost";
  final_chronicle?: string | null;
}

export interface SubmitActionRequest {
  type: "canonical" | "free";
  action_id?: string;
  prompt?: string;
}

export interface SubmitActionResponse {
  state: GameState;
  action_result: ActionResult;
}
