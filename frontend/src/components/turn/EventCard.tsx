import { useState } from "react";
import type { AnchorEvent } from "@/lib/types";
import { BLOCK_CHIP_CLASS } from "@/lib/format";

const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-l-red",
  high: "border-l-orange",
  medium: "border-l-amber",
  low: "border-l-primary",
};
const SEVERITY_LABEL: Record<string, string> = {
  critical: "text-red",
  high: "text-orange",
  medium: "text-amber",
  low: "text-primary",
};

const STATUS_ICON: Record<string, string> = {
  real: "✓",
  altered: "◐",
  averted: "⨯",
  redirected: "→",
};

export function EventCard({ event }: { event: AnchorEvent }) {
  const [expanded, setExpanded] = useState(false);
  const v = event.variant;

  return (
    <div className={`panel-elevated border-l-4 ${SEVERITY_BORDER[event.severity]} p-4 animate-slide-in-up`}>
      <div className="flex items-center gap-2 flex-wrap mb-2">
        <span className={`chip ${SEVERITY_LABEL[event.severity]} border-current/40`}>evento histórico</span>
        <span className="font-mono text-[10px] text-muted-foreground uppercase">severity: {event.severity}</span>
        {event.primaryBlock && <span className={BLOCK_CHIP_CLASS[event.primaryBlock]}>{event.primaryBlock}</span>}
      </div>

      <h3 className="font-serif text-2xl text-foreground mb-2">{event.title}</h3>

      <div className="flex items-center gap-2 mb-3">
        <span className="text-amber font-mono text-lg leading-none">{STATUS_ICON[v.status]}</span>
        <span className="font-mono text-xs text-amber italic">
          variante: <span className="font-semibold not-italic">{v.label}</span>
        </span>
      </div>

      <p className="font-serif text-base text-foreground/90 leading-relaxed">{v.description}</p>

      <button
        onClick={() => setExpanded(e => !e)}
        className="mt-3 font-mono text-[10px] uppercase tracking-widest text-primary/80 hover:text-primary"
      >
        {expanded ? "▾" : "▸"} por que essa variante saiu
      </button>

      {expanded && (
        <div className="mt-3 border-t border-border pt-3 space-y-1.5 animate-fade-in">
          <div className="flex items-baseline justify-between font-mono text-[11px] text-muted-foreground">
            <span>P base</span>
            <span className="tabular-nums text-foreground/70">{v.baseProbability.toFixed(2)}</span>
          </div>
          <div className="flex items-baseline justify-between font-mono text-[11px] text-muted-foreground">
            <span>P efetiva (após modulators)</span>
            <span className="tabular-nums text-amber">{v.actualProbability.toFixed(2)}</span>
          </div>
          {v.modulators.length > 0 && (
            <div className="mt-2">
              <div className="metric-label mb-1">modulators</div>
              {v.modulators.map((m, i) => (
                <div key={i} className="flex items-baseline justify-between font-mono text-[11px] py-0.5">
                  <span className="text-muted-foreground truncate">{m.name}</span>
                  <span className="text-foreground/70 tabular-nums">
                    {m.value} <span className={m.effect > 0 ? "text-green" : "text-red"}>
                      ({m.effect > 0 ? "+" : ""}{m.effect.toFixed(2)})
                    </span>
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
