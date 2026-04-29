import { useEffect, useRef, useState } from "react";

interface TypewriterProps {
  text: string;
  cps?: number;
  className?: string;
  showCursor?: boolean;
  onDone?: () => void;
}

export function Typewriter({ text, cps = 60, className, showCursor = true, onDone }: TypewriterProps) {
  const [n, setN] = useState(0);
  const doneRef = useRef(false);

  useEffect(() => {
    setN(0);
    doneRef.current = false;
    const interval = 1000 / cps;
    let i = 0;
    const id = window.setInterval(() => {
      i += 1;
      setN(i);
      if (i >= text.length) {
        window.clearInterval(id);
        if (!doneRef.current) {
          doneRef.current = true;
          onDone?.();
        }
      }
    }, interval);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, cps]);

  const visible = text.slice(0, n);
  const isDone = n >= text.length;

  return (
    <span
      className={`${className ?? ""} ${showCursor && !isDone ? "cursor-blink" : ""}`}
      // The narrative may contain <em> tags — render as HTML.
      dangerouslySetInnerHTML={{ __html: visible }}
    />
  );
}
