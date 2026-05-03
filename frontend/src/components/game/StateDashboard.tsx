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
  { key: "tech_industry.bigtech_concentration", label: "Bigtech Concentration (US)", source: "block", block: "US" },
  { key: "inequality.gini_intra_block", label: "Gini intra-bloco (US)", source: "block", block: "US" },
  { key: "inequality.gini_between_blocks", label: "Gini entre blocos", source: "global" },
  { key: "financial_markets.global_index", label: "Mercado financeiro", source: "global" },
  { key: "financial_markets.systemic_risk", label: "Risco sistêmico", source: "global" },
];

function getValue(es: EngineState, m: MetricSpec): number | null {
  if (m.source === "global") return es.global_metrics[m.key] ?? null;
  return es.block_metrics[m.key]?.[m.block!] ?? null;
}

export function StateDashboard({ state, prevEngine, prevPlayer }: Props) {
  return (
    <section className="px-6 py-4 space-y-4">
      <LeadAndRiskRow player={state.player_state} prev={prevPlayer ?? null} />
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

// ─────────────────────────────────────────── lab_lead + risk pools (destaque)

function LeadAndRiskRow({ player, prev }: { player: PlayerState; prev: PlayerState | null }) {
  const leadDelta = prev ? player.lab_lead_over_rivals - prev.lab_lead_over_rivals : 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
      {/* Lab Lead — métrica de win mais importante */}
      <div className="border border-amber/60 bg-amber/5 p-4 font-mono">
        <div className="text-[10px] uppercase tracking-widest text-amber/80">
          Lab Lead (vs rivais)
        </div>
        <div className="flex items-baseline justify-between mt-1">
          <div className="text-3xl tabular-nums text-amber">
            {fmtNum(player.lab_lead_over_rivals, 1)}
          </div>
          {Math.abs(leadDelta) > 1e-6 && (
            <span className={`text-xs tabular-nums ${leadDelta > 0 ? "text-green" : "text-red"}`}>
              {fmtDelta(leadDelta, 2)}
            </span>
          )}
        </div>
        <div className="text-[9px] text-muted-foreground mt-1">
          frontier_capability.US − mean(EU, CN, RoW)
        </div>
      </div>

      <RiskBar
        label="Accident Risk"
        value={Math.min(1, Math.max(0, player.accident_risk))}
        prev={prev?.accident_risk}
        baseColor="bg-red"
        thresholdHigh={0.5}
        helpText={`alignment_credit ativo: ${fmtNum(player.alignment_credit, 2)} (drena risco)`}
      />
      <RiskBar
        label="Exposure Risk"
        value={Math.min(1, Math.max(0, player.exposure_risk))}
        prev={prev?.exposure_risk}
        baseColor="bg-block-cn"
        thresholdHigh={0.7}
        helpText="≥1.0 dispara scandal automaticamente"
      />
    </div>
  );
}

function RiskBar({
  label, value, prev, baseColor, thresholdHigh, helpText,
}: {
  label: string;
  value: number;
  prev: number | undefined;
  baseColor: string;
  thresholdHigh: number;
  helpText: string;
}) {
  const pct = value * 100;
  const isHigh = value >= thresholdHigh;
  const delta = prev !== undefined ? value - prev : 0;
  const flash = Math.abs(delta) > 1e-6;
  return (
    <div className={`border ${isHigh ? "border-red" : "border-border"} bg-card/40 p-4 font-mono`}>
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
        {label}
      </div>
      <div className="flex items-baseline justify-between mt-1">
        <div className={`text-3xl tabular-nums ${isHigh ? "text-red" : "text-foreground"}`}>
          {pct.toFixed(0)}%
        </div>
        {flash && (
          <span className={`text-xs tabular-nums ${delta > 0 ? "text-red" : "text-green"}`}>
            {fmtDelta(delta * 100, 0)}%
          </span>
        )}
      </div>
      <div className="mt-2 h-2 bg-card border border-border relative overflow-hidden">
        <motion.div
          className={isHigh ? "bg-red h-full" : `${baseColor} h-full opacity-70`}
          initial={false}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6 }}
        />
      </div>
      <div className="text-[9px] text-muted-foreground mt-1">{helpText}</div>
    </div>
  );
}

// ─────────────────────────────────────────── métricas-mundo cards

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

// ─────────────────────────────────────────── lab_funds / acidentes / reputação

function PlayerStateBar({ player, prev }: { player: PlayerState; prev: PlayerState | null }) {
  const fundsDelta = prev ? player.lab_funds - prev.lab_funds : 0;
  const repDelta = prev ? player.reputation - prev.reputation : 0;

  return (
    <div className="border border-border bg-card/30 px-4 py-3 grid grid-cols-3 gap-3 font-mono">
      <Stat label="Lab Funds" value={fmtNum(player.lab_funds, 2)} delta={fundsDelta} badWhenUp={false} />
      <Stat
        label="Acidentes"
        value={String(player.accidents_count)}
        delta={0}
        badWhenUp
        accentRed={player.accidents_count > 0}
      />
      <Stat label="Reputação" value={fmtNum(player.reputation, 2)} delta={repDelta} badWhenUp={false} />
    </div>
  );
}

function Stat({
  label, value, delta, badWhenUp, accentRed,
}: { label: string; value: string; delta: number; badWhenUp: boolean; accentRed?: boolean }) {
  const flash = Math.abs(delta) > 1e-6;
  const color = flash ? (badWhenUp ? (delta > 0 ? "text-red" : "text-green")
                                   : (delta > 0 ? "text-green" : "text-red")) : "";
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="flex items-baseline gap-2">
        <div className={`text-xl tabular-nums ${accentRed ? "text-red" : "text-foreground"}`}>{value}</div>
        {flash && <span className={`text-xs ${color}`}>{fmtDelta(delta, 2)}</span>}
      </div>
    </div>
  );
}
