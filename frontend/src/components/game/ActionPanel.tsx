import { useState } from "react";
import type { CanonicalAction, GameState } from "@/types/game";

interface Props {
  state: GameState;
  canonicalActions: CanonicalAction[];
  onSubmit: (payload: { type: "canonical" | "free"; action_id?: string; prompt?: string }) => Promise<void>;
  isSubmitting: boolean;
}

export function ActionPanel({ state, canonicalActions, onSubmit, isSubmitting }: Props) {
  const [prompt, setPrompt] = useState("");
  const [selectedCanonical, setSelectedCanonical] = useState<string | null>(null);

  const isGameOver = state.status !== "in_progress";

  function handleChip(action: CanonicalAction) {
    setSelectedCanonical(action.id);
    setPrompt(action.prompt_template);
  }

  function clearSelection() {
    setSelectedCanonical(null);
  }

  async function handleSubmitFree() {
    if (!prompt.trim()) return;
    await onSubmit({ type: "free", prompt: prompt.trim() });
    setPrompt("");
    setSelectedCanonical(null);
  }

  async function handleSubmitCanonical() {
    if (!selectedCanonical) return;
    await onSubmit({ type: "canonical", action_id: selectedCanonical });
    setPrompt("");
    setSelectedCanonical(null);
  }

  return (
    <section className="border-t border-border bg-card/30 px-6 py-4">
      <div className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
        ▰ ação do semestre {state.engine_state.turn_label}
      </div>
      <textarea
        className="w-full font-mono text-sm bg-background border border-border focus:border-primary p-3 min-h-[120px] outline-none disabled:opacity-50"
        placeholder="O que o seu lab faz neste semestre? (escreva em prosa o que decide investir, lançar, lobby, parceria...)"
        value={prompt}
        onChange={(e) => { setPrompt(e.target.value); if (selectedCanonical) clearSelection(); }}
        disabled={isSubmitting || isGameOver}
      />
      <div className="mt-3 flex flex-wrap gap-2 items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {canonicalActions.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => handleChip(a)}
              disabled={isSubmitting || isGameOver}
              title={a.description}
              className={`font-mono text-[11px] uppercase tracking-wider px-2 py-1 border transition-colors disabled:opacity-50 ${
                selectedCanonical === a.id
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-foreground hover:border-primary/50"
              }`}
            >
              {a.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {selectedCanonical ? (
            <button
              type="button"
              onClick={handleSubmitCanonical}
              disabled={isSubmitting || isGameOver}
              className="font-mono text-xs uppercase tracking-widest px-4 py-2 border border-amber text-amber bg-amber/5 hover:bg-amber/15 disabled:opacity-50"
            >
              ▶ submeter como canônica
            </button>
          ) : null}
          <button
            type="button"
            onClick={handleSubmitFree}
            disabled={isSubmitting || isGameOver || !prompt.trim()}
            className="font-mono text-xs uppercase tracking-widest px-4 py-2 border border-primary text-primary bg-primary/10 hover:bg-primary/20 disabled:opacity-50"
          >
            {isSubmitting ? "…processando" : selectedCanonical ? "▶ submeter como livre (editado)" : "▶ submeter ação"}
          </button>
        </div>
      </div>
      {isGameOver && (
        <div className="font-mono text-xs text-amber mt-3">
          Partida encerrada — status: {state.status}.
        </div>
      )}
    </section>
  );
}
