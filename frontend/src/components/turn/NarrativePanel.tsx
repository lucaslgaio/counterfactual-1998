import { useEffect, useState } from "react";
import { Typewriter } from "@/components/Typewriter";
import type { Turn } from "@/lib/types";

interface NarrativePanelProps {
  turn: Turn;
}

export function NarrativePanel({ turn }: NarrativePanelProps) {
  const [done, setDone] = useState(false);
  const paragraphs = turn.narrative.split(/\n\n+/);

  // Reset typewriter when turn changes
  const [activeIdx, setActiveIdx] = useState(0);
  useEffect(() => {
    setActiveIdx(0);
    setDone(false);
  }, [turn.index]);

  const handleParagraphDone = () => {
    if (activeIdx < paragraphs.length - 1) {
      setActiveIdx(i => i + 1);
    } else {
      setDone(true);
    }
  };

  return (
    <div className="panel-elevated border border-primary/30 p-6 glow-cyan">
      <div className="flex items-center justify-between mb-4">
        <span className="section-label">crônica · {turn.label}</span>
        <span className="font-mono text-[10px] text-muted-foreground uppercase tracking-widest">
          lente · <span className="text-primary/80">{turn.lens}</span>
        </span>
      </div>

      <div className="prose-chronicler">
        {paragraphs.map((p, i) => (
          <p key={`${turn.index}-${i}`}>
            {i < activeIdx ? (
              <span dangerouslySetInnerHTML={{ __html: p }} />
            ) : i === activeIdx ? (
              <Typewriter text={p} cps={120} onDone={handleParagraphDone} />
            ) : null}
          </p>
        ))}
      </div>

      {done && (
        <div className="mt-6 pt-3 border-t border-border animate-fade-in">
          <p className="font-mono text-[10px] text-muted-foreground/70 uppercase tracking-widest text-right">
            — turno {turn.index} · {turn.label} · cronista interpretando deltas do motor causal
          </p>
        </div>
      )}
    </div>
  );
}
