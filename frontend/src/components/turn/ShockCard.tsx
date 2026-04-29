import type { ExogenousShock } from "@/lib/types";
import { BLOCK_CHIP_CLASS } from "@/lib/format";

export function ShockCard({ shock }: { shock: ExogenousShock }) {
  return (
    <div className="panel-elevated border-l-4 border-l-magenta p-4 animate-slide-in-up">
      <div className="flex items-center gap-2 flex-wrap mb-2">
        <span className="chip-magenta">choque exógeno</span>
        {shock.primaryBlock && <span className={BLOCK_CHIP_CLASS[shock.primaryBlock]}>{shock.primaryBlock}</span>}
      </div>
      <h3 className="font-serif text-xl text-foreground mb-1">{shock.title}</h3>
      <p className="font-serif text-base text-foreground/85 leading-relaxed">{shock.description}</p>
    </div>
  );
}
