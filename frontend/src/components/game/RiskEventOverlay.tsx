import { motion, AnimatePresence } from "framer-motion";
import type { RiskEvent } from "@/types/game";

interface Props {
  event: RiskEvent | null;
  onDismiss: () => void;
}

/**
 * Overlay dramática que aparece QUANDO accident ou scandal disparam, ANTES
 * do ActionResultModal. O jogador clica pra dispensar e revelar o resto do
 * resultado da ação (com modal padrão depois).
 */
export function RiskEventOverlay({ event, onDismiss }: Props) {
  return (
    <AnimatePresence>
      {event && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4 }}
          className="fixed inset-0 z-[60] bg-red/30 backdrop-blur-md flex items-center justify-center"
          onClick={onDismiss}
        >
          <motion.div
            initial={{ scale: 0.85, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.85, opacity: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="max-w-2xl border-2 border-red bg-background/95 p-8 shadow-[0_0_60px_rgba(220,38,38,0.6)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="font-mono text-[11px] uppercase tracking-[0.4em] text-red mb-3">
              ⚠ {event.kind === "accident" ? "ACIDENTE GRAVE" : "SCANDAL EXPOSTO"} ⚠
            </div>
            <h2 className="font-serif text-3xl text-red leading-tight">
              {event.kind === "accident"
                ? "Algo deu muito errado."
                : "A imprensa descobriu."}
            </h2>
            <p className="font-serif italic text-foreground/90 text-base mt-4 leading-relaxed">
              {event.narrative_seed}
            </p>
            {event.accident_roll !== null && event.accident_roll !== undefined && (
              <div className="font-mono text-[10px] text-muted-foreground mt-4 tabular-nums">
                roll = {event.accident_roll.toFixed(3)} · risk no momento ={" "}
                {(event.risk_at_trigger ?? 0).toFixed(2)}
              </div>
            )}
            <button
              type="button"
              onClick={onDismiss}
              className="mt-6 font-mono text-xs uppercase tracking-widest px-6 py-2 border border-red text-red bg-red/10 hover:bg-red/20"
            >
              Continuar →
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
