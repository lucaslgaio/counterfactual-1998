import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useRunStore, TOTAL_TURNS } from "@/lib/run-store";
import { NarrativePanel } from "@/components/turn/NarrativePanel";
import { EventCard } from "@/components/turn/EventCard";
import { ShockCard } from "@/components/turn/ShockCard";
import { DeltasTable } from "@/components/turn/DeltasTable";
import { DashboardPanel } from "@/components/turn/DashboardPanel";
import { TimelineMini } from "@/components/turn/TimelineMini";
import { BlockMap } from "@/components/turn/BlockMap";
import { DiscourseBar } from "@/components/turn/DiscourseBar";
import { DataSourceChip } from "@/components/DataSourceChip";
import { toast } from "sonner";

export default function TurnView() {
  const { id = "" } = useParams();
  const run = useRunStore(s => s.getRun(id));
  const turns = useRunStore(s => s.getTurns(id));
  const idx = useRunStore(s => s.currentTurnIndex[id] ?? 0);
  const advance = useRunStore(s => s.advanceTurn);
  const goTo = useRunStore(s => s.goToTurn);

  const [advanceN, setAdvanceN] = useState(5);
  const turn = turns[idx];

  if (!run || !turn) {
    return (
      <div className="min-h-screen flex items-center justify-center font-mono text-muted-foreground">
        run não encontrada — <Link to="/runs" className="text-primary ml-2">← voltar</Link>
      </div>
    );
  }

  const handleAdvance = (n = 1) => {
    if (idx >= turns.length - 1) {
      toast("Mock data terminou no turno 24.", {
        description: "Backend SDM ainda em construção — esses dados são placeholders.",
      });
      return;
    }
    for (let i = 0; i < n; i++) advance(id);
  };

  const conf = turn.confidence;
  const confColor = conf === "high" ? "bg-green" : conf === "medium" ? "bg-amber" : "bg-red";

  return (
    <div className="min-h-screen flex flex-col scanlines">
      {/* TURN HEADER */}
      <header className="border-b border-border bg-panel">
        <div className="px-4 py-3 flex items-center gap-4 flex-wrap">
          <Link to="/runs" className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-primary shrink-0">
            ← runs
          </Link>
          <div className="border-l border-border h-6"></div>

          <div className="flex items-baseline gap-3">
            <span className="font-mono text-3xl text-amber tracking-tight tabular-nums">{turn.label}</span>
            <span className="font-mono text-xs text-muted-foreground tabular-nums">
              turno {idx}/{TOTAL_TURNS - 1}
            </span>
          </div>

          <div className="flex items-center gap-1.5 ml-2">
            <div className={`w-2 h-2 ${confColor} rounded-full`} />
            <span className="font-mono text-[10px] uppercase text-muted-foreground">{conf} confidence</span>
          </div>

          <div className="flex-1" />

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleAdvance(1)}
              className="font-mono text-xs uppercase tracking-widest px-4 py-2 border border-primary text-primary bg-primary/5 hover:bg-primary/15 glow-cyan"
            >
              ▶ avançar
            </button>
            <div className="flex">
              <input
                type="number"
                value={advanceN}
                min={1} max={20}
                onChange={e => setAdvanceN(Math.max(1, Math.min(20, Number(e.target.value))))}
                className="w-12 bg-elevated border border-border px-2 py-2 font-mono text-xs tabular-nums focus:border-primary outline-none text-center"
              />
              <button
                onClick={() => handleAdvance(advanceN)}
                className="font-mono text-xs uppercase px-3 py-2 border border-l-0 border-border hover:border-primary/60"
              >
                ⏩
              </button>
            </div>
            <Link
              to={`/runs/${id}/atlas`}
              className="font-mono text-[10px] uppercase tracking-widest px-3 py-2 border border-border hover:border-primary/60 text-muted-foreground hover:text-foreground"
            >
              atlas
            </Link>
          </div>
        </div>

        <div className="px-4 pb-2 font-mono text-[10px] text-muted-foreground truncate">
          run · {run.id} · <span className="text-foreground/70">{run.name}</span> · seed {run.seed} · {run.model}
        </div>
      </header>

      {/* MAIN — 3 columns */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[300px_1fr_400px] gap-3 p-3 min-h-0">
        {/* LEFT — map */}
        <div className="min-h-0">
          <BlockMap turn={turn} />
        </div>

        {/* CENTER — narrative + event + deltas */}
        <div className="space-y-3 overflow-y-auto min-h-0 pr-1">
          {turn.event && <EventCard key={`evt-${turn.index}`} event={turn.event} />}
          {turn.shock && <ShockCard shock={turn.shock} />}

          <NarrativePanel turn={turn} />

          {turn.keyDevelopments.length > 0 && (
            <div className="panel-elevated p-4">
              <div className="section-label mb-3">key developments</div>
              <ul className="space-y-1.5">
                {turn.keyDevelopments.map((kd, i) => (
                  <li key={i} className="font-mono text-[12px] text-foreground/90 flex gap-2 leading-relaxed">
                    <span className="text-primary shrink-0">▸</span>
                    <span>{kd}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <DeltasTable turn={turn} />

          <CausalLinksList turn={turn} />
        </div>

        {/* RIGHT — dashboard */}
        <div className="min-h-0 flex flex-col">
          <DashboardPanel turn={turn} allTurns={turns} />
        </div>
      </div>

      {/* DISCOURSE BAR */}
      <DiscourseBar turn={turn} />

      {/* TIMELINE */}
      <TimelineMini turns={turns} currentIndex={idx} onSelect={(i) => goTo(id, i)} />

      {/* DATA SOURCE INDICATOR */}
      <DataSourceChip runId={id} />
    </div>
  );
}

function CausalLinksList({ turn }: { turn: any }) {
  const links = turn.causalLinks as { source: string; target: string; strength: number; polarity: 1 | -1; scope: string }[];
  if (!links?.length) return null;
  const scopeColor = (s: string) =>
    s === "spillover" ? "text-amber" : s === "global" ? "text-muted-foreground" : "text-block-us";
  return (
    <div className="panel-elevated p-4">
      <div className="section-label mb-3">causal links · turno atual</div>
      <ul className="space-y-1">
        {links.map((l, i) => (
          <li key={i} className="font-mono text-[11px] flex items-center gap-2">
            <span className="text-foreground/80 truncate flex-1">{l.source}</span>
            <span className={`${l.polarity > 0 ? "text-green" : "text-red"} shrink-0`}>
              {l.polarity > 0 ? "→" : "⊣"}
            </span>
            <span className="text-foreground/80 truncate flex-1">{l.target}</span>
            <span className={`text-[9px] uppercase ${scopeColor(l.scope)} shrink-0`}>{l.scope}</span>
            <span className="text-primary tabular-nums shrink-0">{l.strength.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
