import { Link } from "react-router-dom";

export default function Splash() {
  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center starfield scanlines overflow-hidden">
      {/* Top corner — instrument-style metadata */}
      <div className="absolute top-4 left-4 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        cf-1998 // instrument v0.1 // session @ {new Date().toISOString().slice(0, 16).replace("T", " ")}z
      </div>
      <div className="absolute top-4 right-4 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        engine: sdm + chronicler · model: mock
      </div>

      <div className="relative z-10 text-center px-6 max-w-3xl">
        <div className="font-mono text-xs uppercase tracking-[0.4em] text-primary/70 mb-6">
          ▰ counterfactual archive ▰
        </div>

        <h1 className="font-serif font-medium text-amber tracking-tight leading-none"
            style={{ fontSize: "clamp(3rem, 9vw, 6rem)" }}>
          Counterfactual <span className="text-foreground/80">─</span> 1998
        </h1>

        <p className="font-serif italic text-muted-foreground mt-6 text-xl">
          um simulador de mundos que não foram
        </p>

        <div className="mt-12 flex flex-wrap justify-center gap-4">
          <Link
            to="/runs/new"
            className="font-mono text-sm uppercase tracking-widest px-6 py-3 border border-primary text-primary bg-primary/5 hover:bg-primary/15 transition-colors glow-cyan"
          >
            ▶ iniciar nova simulação
          </Link>
          <Link
            to="/runs"
            className="font-mono text-sm uppercase tracking-widest px-6 py-3 border border-border text-foreground hover:border-primary/50 transition-colors"
          >
            ◇ ver runs existentes
          </Link>
          <Link
            to="/manual"
            className="font-mono text-sm uppercase tracking-widest px-6 py-3 border border-border text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
          >
            ❍ glossário das 24 métricas
          </Link>
        </div>

        <div className="mt-16 max-w-md mx-auto border-t border-border pt-4">
          <p className="font-mono text-[11px] text-muted-foreground leading-relaxed">
            instrumento de elicitação contrafactual mediado por llm
            <br />
            system dynamics + cronista interpretativo
            <br />
            <span className="text-primary/60">29 anos · 58 turnos · 24 métricas · 4 blocos · 1998 → 2026</span>
          </p>
        </div>
      </div>
    </div>
  );
}
