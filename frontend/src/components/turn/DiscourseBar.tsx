import { useState } from "react";
import type { Turn } from "@/lib/types";

export function DiscourseBar({ turn }: { turn: Turn }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="border-t border-dashed border-primary/40 bg-elevated/60">
      <div className="px-4 py-2 flex items-center gap-3">
        <button
          onClick={() => setOpen(o => !o)}
          className="font-mono text-[10px] uppercase tracking-widest text-primary/80 hover:text-primary"
        >
          {open ? "▾" : "▸"} discourse · matéria-prima injetada
        </button>
        <div className="flex-1 chip-cyan whitespace-nowrap overflow-hidden text-ellipsis">
          lente: {turn.lens}
        </div>
      </div>
      {open && (
        <div className="px-4 pb-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 animate-fade-in">
          {turn.seeds.map((s, i) => (
            <div key={i} className="border border-border bg-panel p-2.5 group hover:border-primary/50 transition-colors">
              <div className="font-mono text-[9px] uppercase tracking-widest text-amber mb-1">
                {s.year} · {s.domain}
              </div>
              <div className="font-serif text-[12px] text-foreground/85 leading-snug line-clamp-3 group-hover:line-clamp-none">
                {s.text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
