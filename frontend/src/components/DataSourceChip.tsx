import { getDataSource } from "@/lib/run-store";

interface Props {
  runId: string;
}

export function DataSourceChip({ runId }: Props) {
  const src = getDataSource(runId);
  const isReal = src.kind === "real";
  const label = isReal ? `data: real (${src.runId})` : "data: mock";
  const dotClass = isReal ? "bg-green" : "bg-amber";

  return (
    <div
      className="fixed bottom-2 left-2 z-40 flex items-center gap-1.5 px-2 py-1 border border-border bg-panel/80 backdrop-blur-sm pointer-events-none select-none"
      title={isReal ? `loaded from public/runs/${src.fileName}` : "fallback to src/lib/mock-data.ts"}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} style={{ boxShadow: "0 0 4px currentColor" }} />
      <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
    </div>
  );
}
