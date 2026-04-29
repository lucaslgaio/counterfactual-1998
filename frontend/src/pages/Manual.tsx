import { Link } from "react-router-dom";
import { GLOBAL_KEYS, VECTORIZED_KEYS, MATRIX_KEYS, METRICS } from "@/lib/metrics";

export default function Manual() {
  const groups = [
    { title: "globais (12)", keys: GLOBAL_KEYS },
    { title: "vetorizadas por bloco (10)", keys: VECTORIZED_KEYS },
    { title: "matriciais (2)", keys: MATRIX_KEYS },
  ];
  return (
    <div className="min-h-screen scanlines">
      <header className="border-b border-border">
        <div className="container py-4 flex items-center justify-between">
          <Link to="/" className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground hover:text-primary">← cf-1998</Link>
          <h1 className="font-serif text-2xl text-amber">glossário · 24 métricas</h1>
        </div>
      </header>
      <main className="container py-8 max-w-4xl space-y-8">
        {groups.map(g => (
          <section key={g.title}>
            <div className="section-label mb-3">{g.title}</div>
            <div className="space-y-2">
              {g.keys.map(k => {
                const m = METRICS[k as keyof typeof METRICS];
                return (
                  <div key={k} className="panel-elevated p-3 flex justify-between gap-4">
                    <div>
                      <div className="font-mono text-xs text-primary">{k}</div>
                      <div className="font-serif text-base text-foreground">{m.label}</div>
                      <div className="font-mono text-[10px] text-muted-foreground uppercase">{m.domain} · {m.unit}</div>
                    </div>
                    <div className={`font-mono text-[10px] uppercase shrink-0 ${m.badWhenUp ? "text-red" : "text-green"}`}>
                      {m.badWhenUp ? "↑ ruim" : "↑ bom"}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}
