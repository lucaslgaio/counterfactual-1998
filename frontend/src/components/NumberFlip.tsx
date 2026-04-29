import { useEffect, useState } from "react";
import { fmtNum } from "@/lib/format";

interface NumberFlipProps {
  value: number;
  digits?: number;
  className?: string;
  durationMs?: number;
}

/**
 * Animated number with a brief glitch (random rolling digits) before
 * settling on the new value. Honors the value as a tabular number.
 */
export function NumberFlip({ value, digits = 2, className = "", durationMs = 320 }: NumberFlipProps) {
  const [display, setDisplay] = useState<string>(fmtNum(value, digits));
  const [glitching, setGlitching] = useState(false);

  useEffect(() => {
    const target = fmtNum(value, digits);
    if (target === display) return;
    setGlitching(true);
    const start = performance.now();
    let raf = 0;
    const tick = (t: number) => {
      const elapsed = t - start;
      if (elapsed >= durationMs) {
        setDisplay(target);
        setGlitching(false);
        return;
      }
      const scrambled = target
        .split("")
        .map(c => (/[0-9]/.test(c) ? Math.floor(Math.random() * 10).toString() : c))
        .join("");
      setDisplay(scrambled);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, digits]);

  return (
    <span className={`tabular-nums ${glitching ? "text-primary" : ""} ${className}`}>
      {display}
    </span>
  );
}
