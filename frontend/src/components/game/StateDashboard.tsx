import { motion, AnimatePresence } from "framer-motion";
import type { EngineState, GameState, PlayerState } from "@/types/game";
import { fmtNum, fmtDelta } from "@/lib/format";

interface Props {
  state: GameState;
  prevEngine?: EngineState | null;
  prevPlayer?: PlayerState | null;
}

interface MetricSpec {
  key: string;
  label: string;
  source: "global" | "block";
  block?: string;
  highlight?: boolean;
}

const METRICS: MetricSpec[] = [
  { key: "ai_capability.frontier_capability", label: "Frontier Capability (US)", source: "block", block: "US", highlight: true },
  { key: "information_ecosystem.media_trust", label: "Media Trust (global)", source: "global", highlight: true },
  { key: "ai_capability.population_penetration", label: "AI Penetration (US)", source: "block", block: "US" },
  { key: "labor_market.employment_rate", label: "Employment (US)", source: "block", block: "US" },
  { key: "labor_market.automation_exposure", label: "Automation Exposure (US)", source: "block", block: "US" },
  { key: "governance.democracy_index", label: "Democracy (US)", source: "block", block: "US" },
  { key: "governance.ai_regulation_maturity", label: "AI Reg Maturity (US)", source: "block", block: "US" },
  { key: "inequality.gini_intra_block", label: "Gini intra-bloco (US)", source: "block", block: "US" },
  { key: "inequality.gini_between_blocks", label: "Gini entre blocos", source: "global" },
  { key: "financial_markets.global_index", label: "Mercado financeiro", source: "global" },
  { key: "financial_markets.systemic_risk", label: "Risco sistêmico", source: "global" },
  { key: "energy_climate.co2_gt_year", label: "CO₂ Gt/ano", source: "global" },
];

function getValue(es: EngineState, m: MetricSpec): number | null {
  if (m.source === "global") return es.global_metrics[m.key] ?? null;
  return es.block_metrics[m.key]?.[m.block!] ?? null;
}

export function StateDashboard({ state, prevEngine, prevPlayer }: Props) {
  return (
    <section className="px-6 py-4 space-y-4">
      <PlayerStateBar player={state.player_state} prev={prevPlayer ?? null} />
      <div className="grid grid-cols-2 gap-3">
        {METRICS.filter((m) => m.highlight).map((m) => (
          <MetricCard key={m.key + (m.block ?? "")}
            metric={m} state={state} prev={prevEngine ?? null} large />
        ))}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {METRICS.filter((m) => !m.highlight).map((m) => (
          <MetricCard key={m.key + (m.block ?? "")}
            metric={m} state={state} prev={prevEngine ?? null} />
        ))}
      </div>
    </section>
  );
}

function MetricCard({
  metric,
  state,
  prev,
  large,
}: {
  metric: MetricSpec;
  state: GameState;
  prev: EngineState | null;
  large?: boolean;
}) {
  const v = getValue(state.engine_state, metric);
  const vPrev = prev ? getValue(prev, metric) : null;
  const delta = v !== null && vPrev !== null ? v - vPrev : 0;
  const flash = Math.abs(delta) > 1e-6;

  return (
    <div className={`border border-border bg-card/40 ${large ? "p-4" : "p-2"} font-mono`}>
      <div className={`text-muted-foreground uppercase tracking-widest ${large ? "text-[11px]" : "text-[9px]"}`}>
        {metric.label}
      </div>
      <div className="flex items-baseline justify-between mt-1">
        <div className={`tabular-nums text-foreground ${large ? "text-3xl" : "text-lg"}`}>
          {v === null ? "—" : fmtNum(v, 1)}
        </div>
        <AnimatePresence mode="wait">
          {flash && (
            <motion.span
              key={`${metric.key}-${v}`}
              initial={{ opacity: 0, y: -2 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 2 }}
              className={`text-xs tabular-nums ${delta > 0 ? "text-green" : "text-red"}`}
            >
              {fmtDelta(delta, 2)}
            </motion.span>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function PlayerStateBar({ player, prev }: { player: PlayerState; prev: PlayerState | null }) {
  const fundsDelta = prev ? player.lab_funds - prev.lab_funds : 0;
  const repDelta = prev ? player.reputation - prev.reputation : 0;

  return (
    <div className="border border-border bg-card/30 px-4 py-3 grid grid-cols-3 gap-3 font-mono">
      <Stat label="Lab Funds" value={fmtNum(player.lab_funds, 2)} delta={fundsDelta} badWhenUp={false} />
      <Stat label="Acidentes" value={String(player.accidents_count)} delta={0} badWhenUp />
      <Stat label="Reputação" value={fmtNum(player.reputation, 2)} delta={repDelta} badWhenUp={false} />
    </div>
  );
}

function Stat({
  label, value, delta, badWhenUp,
}: { label: string; value: string; delta: number; badWhenUp: boolean }) {
  const flash = Math.abs(delta) > 1e-6;
  const color = flash ? (badWhenUp ? (delta > 0 ? "text-red" : "text-green")
                                   : (delta > 0 ? "text-green" : "text-red")) : "";
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="flex items-baseline gap-2">
        <div className="text-xl tabular-nums text-foreground">{value}</div>
        {flash && <span className={`text-xs ${color}`}>{fmtDelta(delta, 2)}</span>}
      </div>
    </div>
  );
}
