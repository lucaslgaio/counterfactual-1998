import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import type { ActionResult } from "@/types/game";
import { fmtDelta, fmtNum } from "@/lib/format";

interface Props {
  result: ActionResult | null;
  onClose: () => void;
}

export function ActionResultModal({ result, onClose }: Props) {
  if (result === null) return null;
  return (
    <Dialog open={!!result} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-xl font-mono">
        <DialogTitle className="font-serif text-xl text-amber">
          Resolução da ação
        </DialogTitle>
        <Body result={result} />
        <button
          type="button"
          onClick={onClose}
          className="mt-4 self-end font-mono text-xs uppercase tracking-widest px-4 py-2 border border-primary text-primary bg-primary/10 hover:bg-primary/20"
        >
          continuar →
        </button>
      </DialogContent>
    </Dialog>
  );
}

function Body({ result }: { result: ActionResult }) {
  const interp = result.interpretation;
  const cls = interp?.classification ?? (result.action_type === "canonical" ? "canonical" : "—");
  const plausible = interp?.plausible ?? true;

  const outcomeColor =
    result.outcome === "success" ? "text-green"
    : result.outcome === "partial_failure" ? "text-amber"
    : result.outcome === "rejected" ? "text-muted-foreground"
    : "text-red";

  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-center gap-3 text-xs">
        <Chip label={cls} />
        <span className={plausible ? "text-green" : "text-red"}>
          {plausible ? "✓ plausível" : "✗ implausível"}
        </span>
        {result.clipped && <span className="text-amber">⚑ magnitude clipada</span>}
      </div>

      {!plausible && interp?.rejection_reason && (
        <div className="text-xs text-muted-foreground italic border-l-2 border-red pl-3">
          {interp.rejection_reason}
        </div>
      )}

      <div>
        <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">
          success_p · roll · outcome
        </div>
        <RollVisualization successP={interp?.success_p ?? 1} roll={result.roll} />
        <div className={`text-xs mt-1 ${outcomeColor}`}>
          outcome: {result.outcome}
        </div>
      </div>

      <div>
        <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">
          deltas aplicados (motor)
        </div>
        <DeltaList deltas={result.applied_deltas} />
      </div>

      {Object.keys(result.applied_player_deltas).length > 0 && (
        <div>
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">
            deltas aplicados (lab)
          </div>
          <DeltaList deltas={result.applied_player_deltas} highlightRiskPools />
        </div>
      )}

      {result.risk_events.length > 0 && (
        <div className="border border-red bg-red/10 p-3 mt-2">
          <div className="text-[11px] uppercase tracking-widest text-red font-bold">
            ⚠ EVENTO DE RISK POOL
          </div>
          {result.risk_events.map((e, idx) => (
            <div key={idx} className="text-xs text-foreground mt-2">
              <div className="font-bold uppercase">
                {e.kind === "accident" ? "ACIDENTE GRAVE" : "SCANDAL EXPOSTO"}
                {e.accident_roll !== null && e.accident_roll !== undefined && (
                  <span className="text-muted-foreground font-normal ml-2">
                    (roll={fmtNum(e.accident_roll, 3)} vs risk={fmtNum(e.risk_at_trigger ?? 0, 2)})
                  </span>
                )}
              </div>
              <p className="font-serif italic mt-1">{e.narrative_seed}</p>
            </div>
          ))}
        </div>
      )}

      {result.clipped_fields.length > 0 && (
        <div className="text-[10px] text-amber">
          clipados: {result.clipped_fields.join(", ")}
        </div>
      )}
    </div>
  );
}

function Chip({ label }: { label: string }) {
  return (
    <span className="border border-border px-2 py-0.5 text-[10px] uppercase tracking-widest text-foreground">
      {label}
    </span>
  );
}

function RollVisualization({ successP, roll }: { successP: number; roll: number }) {
  const successPct = Math.max(0, Math.min(1, successP)) * 100;
  const rollPct = Math.max(0, Math.min(1, roll)) * 100;
  const half = successPct + (100 - successPct) * 0.5;

  return (
    <div className="relative h-3 bg-card border border-border">
      <div
        className="absolute inset-y-0 left-0 bg-green/30"
        style={{ width: `${successPct}%` }}
      />
      <div
        className="absolute inset-y-0 bg-amber/30"
        style={{ left: `${successPct}%`, width: `${half - successPct}%` }}
      />
      <div
        className="absolute inset-y-0 bg-red/30"
        style={{ left: `${half}%`, width: `${100 - half}%` }}
      />
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-foreground"
        style={{ left: `${rollPct}%` }}
      />
      <div className="absolute -bottom-4 right-0 text-[9px] text-muted-foreground">
        roll={fmtNum(roll, 3)} · success_p={fmtNum(successP, 2)}
      </div>
    </div>
  );
}

const RISK_POOL_FIELDS = new Set(["accident_risk", "exposure_risk", "alignment_credit"]);

function DeltaList({
  deltas,
  highlightRiskPools = false,
}: {
  deltas: Record<string, number>;
  highlightRiskPools?: boolean;
}) {
  const entries = Object.entries(deltas).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  if (entries.length === 0) {
    return <div className="text-xs text-muted-foreground italic">nenhum delta aplicado</div>;
  }
  return (
    <ul className="space-y-1">
      {entries.map(([k, v]) => {
        const isRisk = highlightRiskPools && RISK_POOL_FIELDS.has(k);
        // Para alignment_credit, subir é bom para o jogador (debuff de risk).
        // Para accident_risk e exposure_risk, subir é ruim.
        const goodWhenUp = k === "alignment_credit" || (!isRisk && k !== "accident_risk" && k !== "exposure_risk");
        const color = isRisk
          ? (k === "alignment_credit" ? (v > 0 ? "text-green font-bold" : "text-red font-bold")
                                       : (v > 0 ? "text-red font-bold" : "text-green font-bold"))
          : (v > 0 ? "text-green" : "text-red");
        // unused suppress
        void goodWhenUp;
        return (
          <li key={k} className="flex justify-between text-xs border-b border-border/40 py-0.5">
            <span className="text-foreground/80 truncate">
              {isRisk && "▣ "}{k}
            </span>
            <span className={`tabular-nums ${color}`}>{fmtDelta(v, 3)}</span>
          </li>
        );
      })}
    </ul>
  );
}
