interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  className?: string;
  strokeColor?: string; // raw CSS value, e.g. "hsl(var(--primary))"
}

export function Sparkline({ data, width = 100, height = 24, className, strokeColor }: SparklineProps) {
  if (!data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const stepX = data.length > 1 ? width / (data.length - 1) : 0;
  const points = data
    .map((v, i) => {
      const x = i * stepX;
      const y = height - ((v - min) / span) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const stroke = strokeColor ?? "hsl(var(--primary))";
  return (
    <svg width={width} height={height} className={className} viewBox={`0 0 ${width} ${height}`}>
      <polyline
        fill="none"
        stroke={stroke}
        strokeWidth={1.2}
        strokeLinejoin="round"
        strokeLinecap="round"
        points={points}
      />
      {/* end dot */}
      {data.length > 0 && (
        <circle
          cx={(data.length - 1) * stepX}
          cy={height - ((data[data.length - 1] - min) / span) * height}
          r={1.6}
          fill={stroke}
        />
      )}
    </svg>
  );
}
