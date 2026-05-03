// Cliente HTTP do Modo Jogo. Endpoints servidos por src/api/main.py.
// Base URL: http://localhost:8000 em dev (configurável via VITE_GAME_API_URL).

import type {
  CanonicalAction,
  GameState,
  Mission,
  SubmitActionRequest,
  SubmitActionResponse,
  TurnRecord,
} from "@/types/game";

const BASE_URL =
  (import.meta.env.VITE_GAME_API_URL as string | undefined) ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} → ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as T;
}

export const gameApi = {
  listMissions: () => request<Mission[]>("/game/missions"),

  listCanonicalActions: () => request<CanonicalAction[]>("/game/canonical_actions"),

  createGame: (seed: number, mission_id: string) =>
    request<{ game_id: string; state: GameState }>("/game", {
      method: "POST",
      body: JSON.stringify({ seed, mission_id }),
    }),

  getState: (gameId: string) => request<GameState>(`/game/${gameId}/state`),

  getHistory: (gameId: string) => request<TurnRecord[]>(`/game/${gameId}/history`),

  submitAction: (gameId: string, payload: SubmitActionRequest) =>
    request<SubmitActionResponse>(`/game/${gameId}/action`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
