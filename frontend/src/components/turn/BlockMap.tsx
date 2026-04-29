import { useState } from "react";
import type { Turn, BlockId, VectorizedMetricKey } from "@/lib/types";
import { BLOCKS } from "@/lib/types";
import { VECTORIZED_KEYS, METRICS } from "@/lib/metrics";
import { BLOCK_TEXT_CLASS } from "@/lib/format";

const BLOCK_HSL: Record<BlockId, { h: number; s: number; l: number }> = {
  US:  { h: 213, s: 94, l: 68 },
  EU:  { h: 258, s: 90, l: 76 },
  CN:  { h: 0,   s: 91, l: 71 },
  RoW: { h: 48,  s: 96, l: 53 },
};

const BLOCK_REGIONS: Record<BlockId, { x: number; y: number; w: number; h: number; label: string }> = {
  US:  { x: 30,  y: 80,  w: 140, h: 95,  label: "United States" },
  EU:  { x: 220, y: 70,  w: 80,  h: 70,  label: "European Union" },
  CN:  { x: 360, y: 95,  w: 95,  h: 75,  label: "China" },
  RoW: { x: 30,  y: 195, w: 480, h: 100, label: "Rest of World" },
};

interface BlockMapProps {
  turn: Turn;
}

export function BlockMap({ turn }: BlockMapProps) {
  const [metric, setMetric] = useState<VectorizedMetricKey>("ai_capability.frontier_capability");
  const meta = METRICS[metric];

  const values = BLOCKS.reduce((acc, b) => {
    acc[b] = turn.state.blocks[b][metric];
    return acc;
  }, {} as Record<BlockId, number>);

  const max = Math.max(...Object.values(values));

  return (
    <div className="panel-elevated h-full flex flex-col">
      <div className="border-b border-border p-3 space-y-2">
        <div className="section-label">mapa global · por bloco</div>
        <select
          value={metric}
          onChange={e => setMetric(e.target.value as VectorizedMetricKey)}
          className="w-full bg-panel border border-border px-2 py-1.5 font-mono text-[11px] focus:border-primary outline-none"
        >
          {VECTORIZED_KEYS.map(k => (
            <option key={k} value={k}>{METRICS[k].domain} · {METRICS[k].label}</option>
          ))}
        </select>
      </div>

      <div className="flex-1 p-3 flex items-center justify-center">
        <svg viewBox="0 0 540 320" className="w-full h-auto" style={{ maxHeight: 380 }}>
          {/* grid background */}
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="hsl(213 50% 25%)" strokeWidth="0.4" opacity="0.4" />
            </pattern>
          </defs>
          <rect width="540" height="320" fill="url(#grid)" />

          {/* compass */}
          <text x="510" y="20" textAnchor="end" fill="hsl(187 85% 53% / 0.5)" fontSize="9" fontFamily="JetBrains Mono">N ↑</text>

          {BLOCKS.map(b => {
            const r = BLOCK_REGIONS[b];
            const v = values[b];
            const intensity = max > 0 ? v / max : 0;
            const c = BLOCK_HSL[b];
            const fill = `hsl(${c.h} ${c.s}% ${c.l}% / ${0.15 + intensity * 0.5})`;
            const stroke = `hsl(${c.h} ${c.s}% ${c.l}%)`;
            return (
              <g key={b}>
                <rect
                  x={r.x} y={r.y} width={r.w} height={r.h}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={1.2}
                  className="transition-all"
                />
                <text x={r.x + 6} y={r.y + 14} fill={stroke} fontSize="11" fontFamily="JetBrains Mono" fontWeight="600">{b}</text>
                <text x={r.x + 6} y={r.y + r.h - 8} fill="hsl(213 27% 89%)" fontSize="14" fontFamily="JetBrains Mono" fontWeight="500">
                  {v.toFixed(1)}
                </text>
                {turn.event?.primaryBlock === b && (
                  <g>
                    <rect x={r.x + r.w - 14} y={r.y + 4} width="10" height="10" fill="hsl(48 96% 53%)" opacity="0.85">
                      <animate attributeName="opacity" values="0.4;1;0.4" dur="1.6s" repeatCount="indefinite" />
                    </rect>
                  </g>
                )}
              </g>
            );
          })}

          {/* spillover arrows: largest -> others */}
          {(() => {
            const sorted = [...BLOCKS].sort((a, b) => values[b] - values[a]);
            const src = sorted[0];
            const srcR = BLOCK_REGIONS[src];
            return sorted.slice(1).map(tgt => {
              const tgtR = BLOCK_REGIONS[tgt];
              return (
                <line
                  key={`${src}-${tgt}`}
                  x1={srcR.x + srcR.w / 2} y1={srcR.y + srcR.h / 2}
                  x2={tgtR.x + tgtR.w / 2} y2={tgtR.y + tgtR.h / 2}
                  stroke="hsl(48 96% 53% / 0.35)" strokeWidth="0.8" strokeDasharray="3 3"
                />
              );
            });
          })()}
        </svg>
      </div>

      <div className="border-t border-border px-3 py-2 grid grid-cols-4 gap-1">
        {BLOCKS.map(b => (
          <div key={b} className={`font-mono text-[10px] ${BLOCK_TEXT_CLASS[b]}`}>
            <div className="opacity-70">{b}</div>
            <div className="tabular-nums text-foreground/90">{values[b].toFixed(1)}</div>
          </div>
        ))}
      </div>
      <div className="px-3 pb-2 font-mono text-[9px] text-muted-foreground/70 uppercase tracking-wider">
        {meta.unit} · saturação ∝ valor
      </div>
    </div>
  );
}
