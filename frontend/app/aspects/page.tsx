"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Boxes } from "lucide-react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useAnalysis } from "@/hooks/useAnalysis";
import {
  EmptyState,
  ErrorState,
  GlassCard,
  SentimentBadge,
  Skeleton,
} from "@/components/ui/primitives";
import { SentimentBar } from "@/components/charts/Charts";
import AspectHeatmap from "@/components/aspects/AspectHeatmap";
import { Scene3DBoundary } from "@/components/3d/Scene3DBoundary";
import type { AspectSummary } from "@/lib/types";

// Heavy 3D chart is lazy-loaded and only rendered here on demand.
const Aspect3DChart = dynamic(() => import("@/components/3d/Aspect3DChart"), {
  ssr: false,
  loading: () => <Skeleton className="h-[380px] w-full" />,
});

export default function AspectsPage() {
  const { summary, loading, error } = useAnalysis();

  if (!summary && !loading && !error) {
    return (
      <AppShell>
        <PageHeader title="Aspect Intelligence" />
        <EmptyState
          title="No analysis yet"
          description="Run an analysis first to see aspect-level sentiment."
          action={<Link href="/analysis" className="rounded-xl bg-accent-blue/20 border border-accent-blue/30 px-5 py-2.5 text-sm text-accent-cyan">Analyze Reviews</Link>}
        />
      </AppShell>
    );
  }

  const aspects = summary?.aspects ?? [];

  return (
    <AppShell>
      <PageHeader
        title="Aspect Intelligence"
        subtitle="Mentions, sentiment split and confidence per product aspect."
      />

      {loading && <Skeleton className="h-64 w-full" />}
      {error && <ErrorState message={error} />}

      {summary && (
        <div className="space-y-6">
          {aspects.length === 0 ? (
            <EmptyState title="No aspects detected" description="None of the reviews mention known product aspects." />
          ) : (
            <>
              <div className="grid gap-6 lg:grid-cols-2">
                <GlassCard className="p-5">
                  <h3 className="mb-3 text-sm font-medium text-slate-200">Feature comparison (sentiment %)</h3>
                  <SentimentBar
                    data={aspects.slice(0, 10).map((a) => ({
                      aspect: a.aspect,
                      Positive: a.positive_percentage,
                      Neutral: a.neutral_percentage,
                      Negative: a.negative_percentage,
                    }))}
                    xKey="aspect"
                    stacked
                    bars={[
                      { key: "Positive", color: "#34D399" },
                      { key: "Neutral", color: "#64748B" },
                      { key: "Negative", color: "#FB7185" },
                    ]}
                  />
                </GlassCard>
                <GlassCard className="p-5">
                  <h3 className="mb-3 text-sm font-medium text-slate-200">Sentiment heatmap</h3>
                  <AspectHeatmap aspects={aspects} />
                </GlassCard>
              </div>

              <GlassCard className="p-5">
                <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
                  <Boxes size={15} className="text-accent-cyan" /> 3D aspect explorer
                </h3>
                <Scene3DBoundary>
                  <Aspect3DChart aspects={aspects} />
                </Scene3DBoundary>
              </GlassCard>

              <div className="grid gap-6 md:grid-cols-2">
                <TopList title="Top positive aspects" items={aspects} metric="positive_percentage" color="text-emerald-400" />
                <TopList title="Top negative aspects" items={aspects} metric="negative_percentage" color="text-rose-400" />
              </div>

              <GlassCard className="overflow-hidden p-0">
                <table className="w-full text-sm">
                  <thead className="bg-white/5 text-left text-xs uppercase tracking-wider text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-medium">Aspect</th>
                      <th className="px-4 py-3 font-medium">Mentions</th>
                      <th className="px-4 py-3 font-medium">Positive %</th>
                      <th className="px-4 py-3 font-medium">Neutral %</th>
                      <th className="px-4 py-3 font-medium">Negative %</th>
                      <th className="px-4 py-3 font-medium">Confidence</th>
                      <th className="px-4 py-3 font-medium">Overall</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aspects.map((a) => (
                      <tr key={a.aspect} className="border-t border-white/5 hover:bg-white/[0.03]">
                        <td className="px-4 py-3 font-medium text-slate-200">{a.aspect}</td>
                        <td className="px-4 py-3 font-mono text-slate-400">{a.mention_count}</td>
                        <td className="px-4 py-3 font-mono text-emerald-400">{a.positive_percentage.toFixed(1)}</td>
                        <td className="px-4 py-3 font-mono text-slate-400">{a.neutral_percentage.toFixed(1)}</td>
                        <td className="px-4 py-3 font-mono text-rose-400">{a.negative_percentage.toFixed(1)}</td>
                        <td className="px-4 py-3 font-mono text-slate-400">{(a.average_confidence * 100).toFixed(0)}%</td>
                        <td className="px-4 py-3"><SentimentBadge sentiment={a.overall} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </GlassCard>
            </>
          )}
        </div>
      )}
    </AppShell>
  );
}

function TopList({
  title,
  items,
  metric,
  color,
}: {
  title: string;
  items: AspectSummary[];
  metric: "positive_percentage" | "negative_percentage";
  color: string;
}) {
  const sorted = [...items]
    .sort((a, b) => b[metric] - a[metric])
    .slice(0, 5);
  return (
    <GlassCard className="p-5">
      <h3 className="mb-3 text-sm font-medium text-slate-200">{title}</h3>
      <ul className="space-y-2">
        {sorted.map((a) => (
          <li key={a.aspect} className="flex items-center justify-between text-sm">
            <span className="text-slate-300">{a.aspect}</span>
            <span className={`font-mono text-xs ${color}`}>
              {a[metric].toFixed(0)}% · {a.mention_count} mentions
            </span>
          </li>
        ))}
        {sorted.length === 0 && <li className="text-sm text-slate-500">No data.</li>}
      </ul>
    </GlassCard>
  );
}
