import { Link } from "react-router-dom";
import { useRunStore, TOTAL_TURNS } from "@/lib/run-store";

export default function RunsList() {
  const runs = useRunStore(s => s.runs);

  return (
    <div className="min-h-screen scanlines">
      <header className="border-b border-border">
        <div className="container py-6 flex items-center justify-between">
          <Link to="/" className="font-mono text-xs uppercase tracking-widest text-muted-foreground hover:text-primary">
            ← cf-1998
          </Link>
          <div className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
            runs · {runs.length} registradas
          </div>
        </div>
      </header>

      <main className="container py-10 max-w-5xl">
        <div className="flex items-end justify-between mb-8">
          <div>
            <h1 className="font-serif text-4xl text-amber">runs</h1>
            <p className="font-mono text-xs text-muted-foreground mt-2">
              cada run é uma trajetória contrafactual completa · 58 turnos · seed determinística
            </p>
          </div>
          <Link
            to="/runs/new"
            className="font-mono text-xs uppercase tracking-widest px-4 py-2 border border-primary text-primary bg-primary/5 hover:bg-primary/15"
          >
            + nova run
          </Link>
        </div>

        <div className="space-y-3">
          {runs.map(r => {
            const pct = (r.currentTurn / TOTAL_TURNS) * 100;
            return (
              <Link
                key={r.id}
                to={`/runs/${r.id}`}
                className="block panel p-5 hover:border-primary/60 transition-colors group"
              >
                <div className="flex items-start justify-between gap-6">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                        {r.id}
                      </span>
                      <span className="chip-cyan">{r.aiMode === "big_bang" ? "big bang" : "accel curve"}</span>
                      <span className="chip">{r.playMode}</span>
                      <span className="chip">{r.model.replace("gemini-2.5-", "")}</span>
                    </div>
                    <h3 className="font-serif text-2xl text-foreground group-hover:text-primary transition-colors">
                      {r.name}
                    </h3>
                    {r.notes && (
                      <p className="font-serif italic text-muted-foreground text-sm mt-1">{r.notes}</p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">turno</div>
                    <div className="font-mono text-2xl text-amber tabular-nums">{r.currentTurn}/{TOTAL_TURNS}</div>
                    <div className="font-mono text-[10px] text-muted-foreground tabular-nums mt-1">seed {r.seed}</div>
                  </div>
                </div>
                <div className="mt-4 h-[2px] bg-border relative overflow-hidden">
                  <div
                    className="absolute left-0 top-0 h-full bg-primary"
                    style={{ width: `${pct}%`, boxShadow: "0 0 6px hsl(var(--primary))" }}
                  />
                </div>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
