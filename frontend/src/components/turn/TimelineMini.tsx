import type { Turn } from "@/lib/types";
import { TOTAL_TURNS, MOCK_TURN_LABELS } from "@/lib/run-store";

interface TimelineProps {
  turns: Turn[];
  currentIndex: number;
  onSelect: (idx: number) => void;
}

export function TimelineMini({ turns, currentIndex, onSelect }: TimelineProps) {
  return (
    <div className="border-t border-border bg-panel/80 backdrop-blur-sm">
      <div className="px-4 py-2 flex items-center gap-3">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground shrink-0">
          timeline · 58 turnos
        </span>
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-[2px] min-w-max">
            {Array.from({ length: TOTAL_TURNS }).map((_, i) => {
              const turn = turns[i];
              const completed = i < turns.length;
              const isCurrent = i === currentIndex;
              const event = turn?.event;
              const shock = turn?.shock;
              const label = MOCK_TURN_LABELS[i].label;
              return (
                <div key={i} className="flex flex-col items-center group relative">
                  {/* event flag */}
                  <div className="h-2 mb-[1px]">
                    {event && (
                      <div className="w-0.5 h-2 bg-amber" title={`${event.title} (${event.variant.label})`} />
                    )}
                  </div>
                  <button
                    onClick={() => completed && onSelect(i)}
                    disabled={!completed}
                    className={`w-2 h-7 transition-all ${
                      isCurrent
                        ? "bg-primary pulse-cyan"
                        : completed
                        ? "bg-elevated border border-border hover:border-primary cursor-pointer"
                        : "border border-dashed border-border/40"
                    }`}
                    title={label}
                  />
                  {/* shock flag */}
                  <div className="h-2 mt-[1px]">
                    {shock && <div className="w-0.5 h-2 bg-magenta" title={shock.title} />}
                  </div>

                  {/* hover tooltip */}
                  {turn && (
                    <div className="absolute bottom-full mb-1 hidden group-hover:block z-50 w-64 panel p-2 text-left pointer-events-none">
                      <div className="font-mono text-[10px] text-amber mb-1">{label}</div>
                      <div className="font-serif text-[11px] text-foreground/90 line-clamp-3">
                        {turn.narrative.replace(/<[^>]+>/g, "").slice(0, 120)}…
                      </div>
                      {event && (
                        <div className="mt-1 font-mono text-[9px] text-orange">
                          ▸ {event.title} · {event.variant.label}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
