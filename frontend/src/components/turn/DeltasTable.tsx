import type { Turn } from "@/lib/types";
import { METRICS } from "@/lib/metrics";
import { BLOCKS } from "@/lib/types";
import { fmtDelta, deltaColor, magnitudeBars, BLOCK_TEXT_CLASS } from "@/lib/format";

export function DeltasTable({ turn }: { turn: Turn }) {
  const { global, block } = turn.deltas;

  return (
    <div className="panel-elevated p-4 space-y-5">
      <div className="section-label">deltas · {turn.label}</div>

      {/* GLOBAIS */}
      <div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">▸ globais</div>
        <table className="w-full font-mono text-[11px]">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="text-left py-1.5 font-normal">métrica</th>
              <th className="text-right py-1.5 font-normal w-16">Δ</th>
              <th className="text-right py-1.5 font-normal w-12">mag</th>
              <th className="text-left py-1.5 font-normal pl-3">por quê</th>
            </tr>
          </thead>
          <tbody>
            {global.length === 0 && (
              <tr><td colSpan={4} className="py-2 text-muted-foreground italic">— nenhum delta global significativo</td></tr>
            )}
            {global.map(d => {
              const meta = METRICS[d.key];
              return (
                <tr key={d.key} className="border-b border-border/50">
                  <td className="py-1.5 text-foreground/90 truncate">{meta.label}</td>
                  <td className={`py-1.5 text-right tabular-nums ${deltaColor(d.delta, meta.badWhenUp)}`}>{fmtDelta(d.delta, 3)}</td>
                  <td className="py-1.5 text-right text-primary">{magnitudeBars(d.delta, 1)}</td>
                  <td className="py-1.5 pl-3 text-muted-foreground italic truncate max-w-[200px]">{d.why}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* POR BLOCO */}
      <div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">▸ por bloco</div>
        <table className="w-full font-mono text-[11px]">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="text-left py-1.5 font-normal">métrica</th>
              {BLOCKS.map(b => (
                <th key={b} className={`text-right py-1.5 font-normal w-12 ${BLOCK_TEXT_CLASS[b]}`}>{b}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.map(d => {
              const meta = METRICS[d.key];
              return (
                <tr key={d.key} className="border-b border-border/50">
                  <td className="py-1.5 text-foreground/90 truncate">{meta.label}</td>
                  {BLOCKS.map(b => (
                    <td key={b} className={`py-1.5 text-right tabular-nums ${deltaColor(d.by[b], meta.badWhenUp)}`}>
                      {fmtDelta(d.by[b], 2)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* MATRICIAL — Bilateral tensions heatmap */}
      <BilateralTensionsHeatmap turn={turn} />
    </div>
  );
}

function BilateralTensionsHeatmap({ turn }: { turn: Turn }) {
  const tensions = turn.state.matrix["geopolitics.bilateral_tensions"];
  const prevTensions = turn.prevState.matrix["geopolitics.bilateral_tensions"];

  const getValue = (a: string, b: string) => {
    if (a === b) return null;
    const k1 = `${a}_${b}`;
    const k2 = `${b}_${a}`;
    return tensions[k1] ?? tensions[k2] ?? 0;
  };
  const getDelta = (a: string, b: string) => {
    if (a === b) return 0;
    const k1 = `${a}_${b}`;
    const k2 = `${b}_${a}`;
    const cur = tensions[k1] ?? tensions[k2] ?? 0;
    const prev = prevTensions[k1] ?? prevTensions[k2] ?? 0;
    return cur - prev;
  };

  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">▸ matricial · tensões bilaterais</div>
      <table className="w-full font-mono text-[10px]">
        <thead>
          <tr>
            <th className="w-10"></th>
            {BLOCKS.map(b => (
              <th key={b} className={`px-1 text-center font-normal ${BLOCK_TEXT_CLASS[b]}`}>{b}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {BLOCKS.map(a => (
            <tr key={a}>
              <td className={`text-right pr-2 ${BLOCK_TEXT_CLASS[a]}`}>{a}</td>
              {BLOCKS.map(b => {
                const v = getValue(a, b);
                const d = getDelta(a, b);
                if (v === null) return <td key={b} className="bg-elevated"></td>;
                const intensity = Math.min(1, v / 100);
                return (
                  <td
                    key={b}
                    className="text-center px-1 py-1 border border-border tabular-nums"
                    style={{ background: `hsl(0 84% 60% / ${intensity * 0.4})` }}
                  >
                    <div className="text-foreground">{v.toFixed(0)}</div>
                    {Math.abs(d) > 0.5 && (
                      <div className={`text-[9px] ${d > 0 ? "text-red" : "text-green"}`}>
                        {d > 0 ? "▲" : "▼"}{Math.abs(d).toFixed(1)}
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
