import type { BlockId } from "./types";

export const BLOCK_LABELS: Record<BlockId, string> = {
  US: "United States",
  EU: "European Union",
  CN: "China",
  RoW: "Rest of World",
};

export const BLOCK_COLOR_VAR: Record<BlockId, string> = {
  US: "var(--block-us)",
  EU: "var(--block-eu)",
  CN: "var(--block-cn)",
  RoW: "var(--block-row)",
};

export const BLOCK_TEXT_CLASS: Record<BlockId, string> = {
  US: "text-block-us",
  EU: "text-block-eu",
  CN: "text-block-cn",
  RoW: "text-block-row",
};

export const BLOCK_BG_CLASS: Record<BlockId, string> = {
  US: "bg-block-us",
  EU: "bg-block-eu",
  CN: "bg-block-cn",
  RoW: "bg-block-row",
};

export const BLOCK_CHIP_CLASS: Record<BlockId, string> = {
  US: "chip-block-us",
  EU: "chip-block-eu",
  CN: "chip-block-cn",
  RoW: "chip-block-row",
};

export function fmtNum(n: number, digits = 2): string {
  if (Number.isInteger(n)) return n.toString();
  return n.toFixed(digits);
}

export function fmtDelta(n: number, digits = 2): string {
  const s = fmtNum(Math.abs(n), digits);
  if (n > 0) return `+${s}`;
  if (n < 0) return `−${s}`;
  return "0";
}

export function magnitudeBars(n: number, scale = 1): string {
  const a = Math.abs(n) / scale;
  if (a > 3) return "▲▲▲";
  if (a > 1) return "▲▲";
  if (a > 0.3) return "▲";
  if (a > 0.05) return "·";
  return "";
}

export function deltaColor(delta: number, badWhenUp: boolean): string {
  if (Math.abs(delta) < 0.001) return "text-muted-foreground";
  const isGood = badWhenUp ? delta < 0 : delta > 0;
  return isGood ? "text-green" : "text-red";
}
