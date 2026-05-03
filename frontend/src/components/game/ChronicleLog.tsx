import type { TurnRecord } from "@/types/game";

interface Props {
  history: TurnRecord[];
}

export function ChronicleLog({ history }: Props) {
  if (history.length === 0) {
    return (
      <div className="font-mono text-xs text-muted-foreground p-4 border border-dashed border-border">
        Nenhum semestre jogado ainda. Submeta sua primeira ação para começar a história do seu lab.
      </div>
    );
  }
  // Mais recente no topo
  const ordered = [...history].slice().reverse();
  return (
    <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
      {ordered.map((rec) => (
        <ChronicleItem key={`${rec.turn}-${rec.turn_label}`} rec={rec} />
      ))}
    </div>
  );
}

function ChronicleItem({ rec }: { rec: TurnRecord }) {
  const ar = rec.action_result;
  const outcomeColor =
    ar.outcome === "success" ? "text-green"
    : ar.outcome === "partial_failure" ? "text-amber"
    : ar.outcome === "rejected" ? "text-muted-foreground"
    : "text-red";
  const cls = ar.interpretation?.classification ?? "canonical";

  return (
    <article className="border border-border bg-card/40 p-3">
      <header className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground flex items-center justify-between">
        <span>Turno {rec.turn} · {rec.turn_label}</span>
        <span>
          <span className="text-foreground/70">{cls}</span>
          {" · "}
          <span className={outcomeColor}>{ar.outcome}</span>
        </span>
      </header>
      <p className="font-serif text-sm text-foreground/90 mt-2 leading-relaxed">
        {rec.chronicle}
      </p>
      <details className="mt-2 font-mono text-[10px] text-muted-foreground">
        <summary className="cursor-pointer hover:text-foreground">ação tomada</summary>
        <p className="mt-1 italic">{ar.raw_input}</p>
      </details>
    </article>
  );
}
