import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { gameApi } from "@/api/gameApi";
import { ActionPanel } from "@/components/game/ActionPanel";
import { ActionResultModal } from "@/components/game/ActionResultModal";
import { ChronicleLog } from "@/components/game/ChronicleLog";
import { MissionHeader } from "@/components/game/MissionHeader";
import { RiskEventOverlay } from "@/components/game/RiskEventOverlay";
import { StateDashboard } from "@/components/game/StateDashboard";
import type {
  ActionResult,
  CanonicalAction,
  EngineState,
  GameState,
  PlayerState,
  RiskEvent,
  SubmitActionRequest,
} from "@/types/game";

export default function Play() {
  const [searchParams, setSearchParams] = useSearchParams();
  const gameIdFromUrl = searchParams.get("g");
  const seedFromUrl = Number(searchParams.get("seed") ?? 42);

  const [gameId, setGameId] = useState<string | null>(gameIdFromUrl);
  const [lastResult, setLastResult] = useState<ActionResult | null>(null);
  const [pendingRiskEvent, setPendingRiskEvent] = useState<RiskEvent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const prevEngineRef = useRef<EngineState | null>(null);
  const prevPlayerRef = useRef<PlayerState | null>(null);

  const queryClient = useQueryClient();

  // Catálogo das ações canônicas
  const canonicalActionsQuery = useQuery({
    queryKey: ["canonical_actions"],
    queryFn: () => gameApi.listCanonicalActions(),
    staleTime: 1000 * 60 * 60,
  });

  // Estado da partida
  const stateQuery = useQuery({
    queryKey: ["game_state", gameId],
    queryFn: () => gameApi.getState(gameId!),
    enabled: !!gameId,
  });

  // Cria partida se nenhuma existir
  const createMutation = useMutation({
    mutationFn: () => gameApi.createGame(seedFromUrl, "agi_aligned"),
    onSuccess: (data) => {
      setGameId(data.game_id);
      setSearchParams({ g: data.game_id, seed: String(seedFromUrl) }, { replace: true });
      queryClient.setQueryData(["game_state", data.game_id], data.state);
    },
    onError: (e: Error) => setError(e.message),
  });

  useEffect(() => {
    if (!gameId && !createMutation.isPending) {
      createMutation.mutate();
    }
    // só dispara uma vez no mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Submeter ação
  const actionMutation = useMutation({
    mutationFn: (payload: SubmitActionRequest) =>
      gameApi.submitAction(gameId!, payload),
    onSuccess: (data) => {
      // Captura "before" antes de substituir
      const current = queryClient.getQueryData<GameState>(["game_state", gameId]);
      if (current) {
        prevEngineRef.current = current.engine_state;
        prevPlayerRef.current = current.player_state;
      }
      queryClient.setQueryData(["game_state", gameId], data.state);
      // Se há risk event, mostra overlay primeiro; modal padrão sai depois.
      if (data.action_result.risk_events.length > 0) {
        setPendingRiskEvent(data.action_result.risk_events[0]);
      }
      setLastResult(data.action_result);
      setError(null);
    },
    onError: (e: Error) => setError(e.message),
  });

  const state = stateQuery.data;
  const canonicalActions: CanonicalAction[] = canonicalActionsQuery.data ?? [];

  if (createMutation.isPending || stateQuery.isLoading || !state) {
    return <LoadingScreen />;
  }

  return (
    <div className="min-h-screen bg-background text-foreground starfield scanlines">
      <TopNav />
      {error && (
        <div className="bg-red/10 border-y border-red px-6 py-2 font-mono text-xs text-red">
          {error}
        </div>
      )}
      <MissionHeader state={state} />

      <main className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6 px-2 mt-2">
        <div className="space-y-2">
          <StateDashboard
            state={state}
            prevEngine={prevEngineRef.current}
            prevPlayer={prevPlayerRef.current}
          />
          <ActionPanel
            state={state}
            canonicalActions={canonicalActions}
            isSubmitting={actionMutation.isPending}
            onSubmit={async (payload) => { await actionMutation.mutateAsync(payload); }}
          />
        </div>
        <aside className="px-4 py-4">
          <h2 className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
            ▰ crônica
          </h2>
          <ChronicleLog history={state.history} />
        </aside>
      </main>

      {state.status !== "in_progress" && (
        <FinalScreen state={state} />
      )}

      <RiskEventOverlay
        event={pendingRiskEvent}
        onDismiss={() => setPendingRiskEvent(null)}
      />
      <ActionResultModal
        result={pendingRiskEvent ? null : lastResult}
        onClose={() => setLastResult(null)}
      />
    </div>
  );
}

function TopNav() {
  return (
    <nav className="border-b border-border px-6 py-2 flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
      <span>cf-1998 // play mode</span>
      <div className="flex gap-4">
        <Link to="/" className="hover:text-primary">◇ início</Link>
        <Link to="/manual" className="hover:text-primary">❍ manual</Link>
      </div>
    </nav>
  );
}

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center font-mono text-sm text-muted-foreground">
      …carregando partida
    </div>
  );
}

function FinalScreen({ state }: { state: GameState }) {
  const won = state.status === "won";
  return (
    <section className="border-t border-border bg-card/40 px-6 py-6 mt-4">
      <h2 className={`font-serif text-3xl ${won ? "text-green" : "text-red"}`}>
        {won ? "Vitória" : "Derrota"} — {state.mission.name}
      </h2>
      <p className="font-mono text-sm text-foreground/80 mt-2">
        {state.final_chronicle ?? "—"}
      </p>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
        <div>
          <h3 className="uppercase tracking-widest text-muted-foreground">vitória</h3>
          <ul className="mt-1 space-y-1">
            {state.mission.win_conditions.map((c) => (
              <li key={c.metric}>{c.metric} {c.operator} {c.threshold}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="uppercase tracking-widest text-muted-foreground">derrota</h3>
          <ul className="mt-1 space-y-1">
            {state.mission.lose_conditions.map((c) => (
              <li key={c.metric}>{c.metric} {c.operator} {c.threshold}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
