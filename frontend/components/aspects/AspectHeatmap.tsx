"use client";

/**
 * Aspect sentiment heatmap: aspects x sentiment with color intensity.
 * Pure CSS — fast for any dataset size.
 */
import type { AspectSummary } from "@/lib/types";

function cellColor(pct: number, kind: "pos" | "neu" | "neg"): string {
  const alpha = Math.min(0.75, pct / 100 + 0.06);
  const base = kind === "pos" ? "52, 211, 153" : kind === "neg" ? "251, 113, 133" : "148, 163, 184";
  return `rgba(${base}, ${alpha.toFixed(2)})`;
}

export default function AspectHeatmap({ aspects }: { aspects: AspectSummary[] }) {
  if (!aspects.length) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" aria-label="Aspect sentiment heatmap">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wider text-slate-500">
            <th className="px-3 py-2 font-medium">Aspect</th>
            <th className="px-3 py-2 font-medium text-right">Positive</th>
            <th className="px-3 py-2 font-medium text-right">Neutral</th>
            <th className="px-3 py-2 font-medium text-right">Negative</th>
            <th className="px-3 py-2 font-medium text-right">Mentions</th>
          </tr>
        </thead>
        <tbody>
          {aspects.map((a) => (
            <tr key={a.aspect} className="border-t border-white/5">
              <td className="px-3 py-2 font-medium text-slate-200">{a.aspect}</td>
              <td className="px-3 py-2 text-right font-mono text-emerald-300" style={{ background: cellColor(a.positive_percentage, "pos"), borderRadius: 6 }}>
                {a.positive_percentage.toFixed(0)}%
              </td>
              <td className="px-3 py-2 text-right font-mono text-slate-300" style={{ background: cellColor(a.neutral_percentage, "neu"), borderRadius: 6 }}>
                {a.neutral_percentage.toFixed(0)}%
              </td>
              <td className="px-3 py-2 text-right font-mono text-rose-300" style={{ background: cellColor(a.negative_percentage, "neg"), borderRadius: 6 }}>
                {a.negative_percentage.toFixed(0)}%
              </td>
              <td className="px-3 py-2 text-right font-mono text-slate-400">{a.mention_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
