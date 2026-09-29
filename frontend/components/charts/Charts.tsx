"use client";

/** Recharts wrappers tuned for the dark glass theme. */
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts";

const TOOLTIP_STYLE = {
  backgroundColor: "rgba(11, 16, 32, 0.95)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 12,
  color: "#E2E8F0",
  fontSize: 12,
};

export function SentimentPie({
  data,
}: {
  data: { name: string; value: number }[];
}) {
  const COLORS: Record<string, string> = {
    Positive: "#34D399",
    Neutral: "#94A3B8",
    Negative: "#FB7185",
    Mixed: "#FBBF24",
  };
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} paddingAngle={3} strokeWidth={0}>
          {data.map((d) => (
            <Cell key={d.name} fill={COLORS[d.name] ?? "#64748B"} />
          ))}
        </Pie>
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: "#94A3B8" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function SentimentBar({
  data,
  xKey,
  bars,
  height = 280,
  stacked = false,
}: {
  data: Record<string, unknown>[];
  xKey: string;
  bars: { key: string; color: string; name?: string }[];
  height?: number;
  stacked?: boolean;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis dataKey={xKey} tick={{ fill: "#94A3B8", fontSize: 11 }} interval={0} angle={data.length > 6 ? -25 : 0} height={data.length > 6 ? 60 : 30} textAnchor={data.length > 6 ? "end" : "middle"} />
        <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} />
        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        {bars.length > 1 && <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: "#94A3B8" }} />}
        {bars.map((b) => (
          <Bar
            key={b.key}
            dataKey={b.key}
            name={b.name ?? b.key}
            fill={b.color}
            radius={[6, 6, 0, 0]}
            stackId={stacked ? "a" : undefined}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function QualityGauge({ score, label }: { score: number; label: string }) {
  const color = score >= 80 ? "#34D399" : score >= 60 ? "#FBBF24" : "#FB7185";
  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={180}>
        <RadialBarChart
          data={[{ name: label, value: score }]}
          innerRadius="70%"
          outerRadius="100%"
          startAngle={210}
          endAngle={-30}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar dataKey="value" cornerRadius={12} fill={color} background={{ fill: "rgba(255,255,255,0.05)" }} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center pt-4">
        <span className="text-3xl font-semibold" style={{ color }}>
          {Math.round(score)}
        </span>
        <span className="text-xs text-slate-500">{label}</span>
      </div>
    </div>
  );
}

export function QualityRadar({
  scores,
}: {
  scores: { dimension: string; score: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={scores} outerRadius="72%">
        <PolarGrid stroke="rgba(255,255,255,0.08)" />
        <PolarAngleAxis dataKey="dimension" tick={{ fill: "#94A3B8", fontSize: 11 }} />
        <Radar dataKey="score" stroke="#22D3EE" fill="#22D3EE" fillOpacity={0.25} />
        <Tooltip contentStyle={TOOLTIP_STYLE} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

export function ConfidenceHistogramChart({
  buckets,
  counts,
}: {
  buckets: string[];
  counts: number[];
}) {
  const data = buckets.map((b, i) => ({ bucket: b, count: counts[i] }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis dataKey="bucket" tick={{ fill: "#94A3B8", fontSize: 11 }} />
        <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} allowDecimals={false} />
        <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
        <Bar dataKey="count" fill="#3B82F6" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
