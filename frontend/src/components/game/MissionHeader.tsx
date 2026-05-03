import type { Condition, GameState, Mission } from "@/types/game";
import { fmtNum } from "@/lib/format";
import { evalConditionValue } from "./conditionUtils";

interface Props {
  state: GameState;
}

const HORIZON_TURNS = 10;

export function MissionHeader({ state }: Props) {
  const m: Mission = state.mission;
  const turn = state.current_turn;
  const yearLabel = state.engine_state.turn_label;

  return (
    <header className="border-b border-border px-6 py-4 bg-background/80 backdrop-blur">
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            ▰ missão ativa
          </div>
          <h1 className="font-serif text-2xl text-amber leading-tight mt-1">{m.name}</h1>
          <p className="font-mono text-xs text-muted-foreground max-w-xl mt-1">{m.description}</p>
        </div>

        <div className="font-mono text-right">
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground">turno</div>
          <div className="text-2xl text-primary tabular-nums">
            {turn}<span className="text-muted-foreground">/{HORIZON_TURNS}</span>
          </div>
          <div className="text-xs text-muted-foreground mt-1">{yearLabel}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
        {m.win_conditions.map((c) => (
          <ConditionBar key={`win-${c.metric}`} cond={c} state={state} positive />
        ))}
      </div>
      <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-3">
        {m.lose_conditions.map((c) => (
          <ConditionBar key={`lose-${c.metric}`} cond={c} state={state} positive={false} />
        ))}
      </div>
    </header>
  );
}

function ConditionBar({
  cond,
  state,
  positive,
}: {
  cond: Condition;
  state: GameState;
  positive: boolean;
}) {
  const value = evalConditionValue(cond, state);
  const ok = isConditionMet(cond, value);
  const tone = positive
    ? ok
      ? "border-green/50 text-green"
      : "border-border text-foreground"
    : ok
      ? "border-red/60 text-red"
      : "border-border text-muted-foreground";

  const valueStr = value !== null && Number.isFinite(value) ? fmtNum(value, 2) : "—";

  return (
    <div className={`border ${tone} px-3 py-2 font-mono text-xs flex items-center justify-between`}>
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">{positive ? "vitória" : "derrota"}:</span>
        <span>{cond.metric}</span>
      </div>
      <div className="tabular-nums">
        <span className="text-muted-foreground">{cond.operator}</span>{" "}
        <span>{fmtNum(cond.threshold, 2)}</span>{" · "}
        <span className="text-foreground">{valueStr}</span>
      </div>
    </div>
  );
}

function isConditionMet(cond: Condition, value: number | null): boolean {
  if (value === null || !Number.isFinite(value)) return false;
  switch (cond.operator) {
    case ">=": return value >= cond.threshold;
    case "<=": return value <= cond.threshold;
    case ">": return value > cond.threshold;
    case "<": return value < cond.threshold;
    case "==": return value === cond.threshold;
    case "!=": return value !== cond.threshold;
  }
}
