import { Link, useParams } from "react-router-dom";
import { useRunStore } from "@/lib/run-store";
import { GLOBAL_KEYS, VECTORIZED_KEYS, METRICS } from "@/lib/metrics";
import { BLOCKS } from "@/lib/types";
import { Sparkline } from "@/components/Sparkline";
import { BLOCK_TEXT_CLASS } from "@/lib/format";

const BLOCK_HSL: Record<string, string> = {
  US: "hsl(213 94% 68%)", EU: "hsl(258 90% 76%)",
  CN: "hsl(0 91% 71%)", RoW: "hsl(48 96% 53%)",
};

export default function Atlas() {
  const { id = "" } = useParams();
  const run = useRunStore(s => s.getRun(id));
  const turns = useRunStore(s => s.getTurns(id));

  if (!run) return <div className="p-10 font-mono">run não encontrada</div>;

  return (
    <div className="min-h-screen scanlines">
      <header className="border-b border-border">
        <div className="px-4 py-4 flex items-center justify-between">
          <Link to={`/runs/${id}`} className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-primary">
            ← turno
          </Link>
          <div>
            <h1 className="font-serif text-2xl text-amber">atlas · {run.name}</h1>
            <div className="font-mono text-[10px] text-muted-foreground text-right">{turns.length} turnos · {run.id}</div>
          </div>
        </div>
      </header>

      <main className="p-6 space-y-8 max-w-7xl mx-auto">
        <section>
          <div className="section-label mb-4">trajetórias globais · 12 métricas</div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {GLOBAL_KEYS.map(k => {
              const meta = METRICS[k];
              const series = turns.map(t => t.state.global[k]);
              return (
                <div key={k} className="panel-elevated p-3">
                  <div className="metric-label truncate">{meta.label}</div>
                  <div className="font-mono text-lg text-foreground tabular-nums mt-1">{series[series.length - 1]?.toFixed(2)}</div>
                  <Sparkline data={series} width={200} height={36} />
                </div>
              );
            })}
          </div>
        </section>

        <section>
          <div className="section-label mb-4">trajetórias por bloco · vetorizadas</div>
          <div className="space-y-3">
            {VECTORIZED_KEYS.slice(0, 6).map(k => {
              const meta = METRICS[k];
              return (
                <div key={k} className="panel-elevated p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="metric-label">{meta.domain} · {meta.label}</div>
                    <div className="font-mono text-[9px] text-muted-foreground">{meta.unit}</div>
                  </div>
                  <div className="grid grid-cols-4 gap-3">
                    {BLOCKS.map(b => {
                      const series = turns.map(t => t.state.blocks[b][k]);
                      return (
                        <div key={b}>
                          <div className={`font-mono text-[10px] ${BLOCK_TEXT_CLASS[b]} mb-1`}>{b} · {series[series.length-1]?.toFixed(1)}</div>
                          <Sparkline data={series} width={180} height={28} strokeColor={BLOCK_HSL[b]} />
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section>
          <div className="section-label mb-4">cronologia narrativa · síntese por turno</div>
          <div className="space-y-2">
            {turns.map(t => (
              <div key={t.index} className="panel-elevated p-3 flex gap-4">
                <div className="font-mono text-amber text-sm tabular-nums shrink-0 w-16">{t.label}</div>
                <div className="flex-1">
                  {t.event && (
                    <div className="chip-amber inline-block mb-1">{t.event.title} · {t.event.variant.label}</div>
                  )}
                  <div className="font-serif text-[13px] text-foreground/85 line-clamp-2">
                    {t.narrative.replace(/<[^>]+>/g, "").slice(0, 240)}…
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
