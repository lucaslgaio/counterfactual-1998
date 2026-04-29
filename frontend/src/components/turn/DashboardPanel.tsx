import { useState } from "react";
import type { Turn, BlockId } from "@/lib/types";
import { BLOCKS } from "@/lib/types";
import { GLOBAL_KEYS, VECTORIZED_KEYS, METRICS } from "@/lib/metrics";
import { Sparkline } from "@/components/Sparkline";
import { NumberFlip } from "@/components/NumberFlip";
import { BLOCK_TEXT_CLASS, fmtNum, fmtDelta, deltaColor } from "@/lib/format";

type Tab = "global" | BlockId | "matrix";

export function DashboardPanel({ turn, allTurns }: { turn: Turn; allTurns: Turn[] }) {
  const [tab, setTab] = useState<Tab>("global");

  const tabs: { v: Tab; l: string; cls?: string }[] = [
    { v: "global", l: "globais" },
    { v: "US", l: "US", cls: "text-block-us" },
    { v: "EU", l: "EU", cls: "text-block-eu" },
    { v: "CN", l: "CN", cls: "text-block-cn" },
    { v: "RoW", l: "RoW", cls: "text-block-row" },
    { v: "matrix", l: "matriz" },
  ];

  return (
    <div className="panel-elevated h-full flex flex-col">
      <div className="border-b border-border flex">
        {tabs.map(t => {
          const active = tab === t.v;
          return (
            <button
              key={t.v}
              onClick={() => setTab(t.v)}
              className={`flex-1 px-2 py-2.5 font-mono text-[10px] uppercase tracking-widest border-r border-border last:border-r-0 transition-colors ${
                active ? "bg-primary/10 text-primary border-b-2 border-b-primary -mb-px" : `${t.cls ?? "text-muted-foreground"} hover:bg-elevated`
              }`}
            >
              {t.l}
            </button>
          );
        })}
      </div>

      <div className="p-4 overflow-y-auto flex-1">
        {tab === "global" && <GlobalGrid turn={turn} allTurns={allTurns} />}
        {(tab === "US" || tab === "EU" || tab === "CN" || tab === "RoW") && (
          <BlockGrid turn={turn} allTurns={allTurns} block={tab as BlockId} />
        )}
        {tab === "matrix" && <MatrixView turn={turn} />}
      </div>
    </div>
  );
}

function GlobalGrid({ turn, allTurns }: { turn: Turn; allTurns: Turn[] }) {
  const upToHere = allTurns.slice(0, turn.index + 1);
  return (
    <div className="grid grid-cols-2 gap-2.5">
      {GLOBAL_KEYS.map(k => {
        const meta = METRICS[k];
        const series = upToHere.map(t => t.state.global[k]);
        const prev = turn.prevState.global[k];
        const cur = turn.state.global[k];
        const delta = cur - prev;
        return (
          <div key={k} className="border border-border bg-panel p-3">
            <div className="metric-label truncate" title={meta.label}>{meta.label}</div>
            <div className="mt-1 flex items-baseline justify-between gap-2">
              <NumberFlip value={cur} digits={2} className="font-mono text-xl text-foreground" />
              <span className={`font-mono text-[10px] tabular-nums ${deltaColor(delta, meta.badWhenUp)}`}>
                {fmtDelta(delta, 2)}
              </span>
            </div>
            <div className="mt-1.5">
              <Sparkline data={series} width={140} height={20} />
            </div>
            <div className="font-mono text-[9px] text-muted-foreground/70 mt-1 uppercase tracking-wider">{meta.unit}</div>
          </div>
        );
      })}
    </div>
  );
}

function BlockGrid({ turn, allTurns, block }: { turn: Turn; allTurns: Turn[]; block: BlockId }) {
  const upToHere = allTurns.slice(0, turn.index + 1);
  const blockColors: Record<BlockId, string> = {
    US: "hsl(var(--block-us))", EU: "hsl(var(--block-eu))",
    CN: "hsl(var(--block-cn))", RoW: "hsl(var(--block-row))",
  };
  return (
    <>
      <div className={`mb-3 pb-2 border-b border-border ${BLOCK_TEXT_CLASS[block]} font-mono text-xs uppercase tracking-widest`}>
        bloco {block} · 10 métricas vetorizadas
      </div>
      <div className="grid grid-cols-2 gap-2.5">
        {VECTORIZED_KEYS.map(k => {
          const meta = METRICS[k];
          const series = upToHere.map(t => t.state.blocks[block][k]);
          const prev = turn.prevState.blocks[block][k];
          const cur = turn.state.blocks[block][k];
          const delta = cur - prev;
          return (
            <div key={k} className="border border-border bg-panel p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <div className={`w-1.5 h-1.5 ${`bg-block-${block.toLowerCase()}`}`} style={{ backgroundColor: blockColors[block] }} />
                <div className="metric-label truncate flex-1" title={meta.label}>{meta.label}</div>
              </div>
              <div className="flex items-baseline justify-between gap-2">
                <NumberFlip value={cur} digits={2} className="font-mono text-xl text-foreground" />
                <span className={`font-mono text-[10px] tabular-nums ${deltaColor(delta, meta.badWhenUp)}`}>
                  {fmtDelta(delta, 2)}
                </span>
              </div>
              <div className="mt-1.5">
                <Sparkline data={series} width={140} height={20} strokeColor={blockColors[block]} />
              </div>
              <div className="font-mono text-[9px] text-muted-foreground/70 mt-1 uppercase tracking-wider">{meta.unit}</div>
            </div>
          );
        })}
      </div>
    </>
  );
}

function MatrixView({ turn }: { turn: Turn }) {
  const tens = turn.state.matrix["geopolitics.bilateral_tensions"];
  const prevTens = turn.prevState.matrix["geopolitics.bilateral_tensions"];
  return (
    <div className="space-y-5">
      <div>
        <div className="metric-label mb-2">tensões bilaterais (heatmap)</div>
        <table className="w-full font-mono text-[11px]">
          <thead>
            <tr>
              <th className="w-10"></th>
              {BLOCKS.map(b => <th key={b} className={`text-center font-normal ${BLOCK_TEXT_CLASS[b]}`}>{b}</th>)}
            </tr>
          </thead>
          <tbody>
            {BLOCKS.map(a => (
              <tr key={a}>
                <td className={`text-right pr-2 ${BLOCK_TEXT_CLASS[a]}`}>{a}</td>
                {BLOCKS.map(b => {
                  if (a === b) return <td key={b} className="bg-elevated"></td>;
                  const k1 = `${a}_${b}`, k2 = `${b}_${a}`;
                  const v = tens[k1] ?? tens[k2] ?? 0;
                  const pv = prevTens[k1] ?? prevTens[k2] ?? 0;
                  const d = v - pv;
                  return (
                    <td key={b} className="text-center py-2 border border-border tabular-nums"
                        style={{ background: `hsl(0 84% 60% / ${(v/100)*0.45})` }}>
                      <div>{v.toFixed(0)}</div>
                      {Math.abs(d) > 0.3 && <div className={`text-[9px] ${d>0?"text-red":"text-green"}`}>{d>0?"▲":"▼"}{Math.abs(d).toFixed(1)}</div>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border border-border bg-panel p-3">
        <div className="metric-label">conflitos ativos</div>
        <div className="metric-value mt-1">{fmtNum(turn.state.matrix["geopolitics.active_conflicts"], 0)}</div>
      </div>
    </div>
  );
}
