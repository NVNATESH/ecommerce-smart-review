"use client";

import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useAnalysis } from "@/hooks/useAnalysis";
import {
  EmptyState,
  ErrorState,
  GlassCard,
  MetricCard,
  Skeleton,
  StatusBadge,
} from "@/components/ui/primitives";
import { QualityGauge, QualityRadar } from "@/components/charts/Charts";

export default function QualityPage() {
  const { summary, loading, error } = useAnalysis();

  if (!summary && !loading && !error) {
    return (
      <AppShell>
        <PageHeader title="Review Quality" />
        <EmptyState
          title="No analysis yet"
          description="Run an analysis first to see the dataset quality report."
          action={<Link href="/analysis" className="rounded-xl bg-accent-blue/20 border border-accent-blue/30 px-5 py-2.5 text-sm text-accent-cyan">Analyze Reviews</Link>}
        />
      </AppShell>
    );
  }

  const q = summary?.quality;

  return (
    <AppShell>
      <PageHeader
        title="Review Quality"
        subtitle="Transparent component scores combined into one dataset decision."
      />

      {loading && <Skeleton className="h-64 w-full" />}
      {error && <ErrorState message={error} />}

      {summary && q && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Total Rows" value={q.total_rows} />
            <MetricCard label="Valid Reviews" value={q.valid_reviews} accent="text-accent-emerald" />
            <MetricCard label="Uncertain" value={q.uncertain_reviews} accent="text-accent-amber" />
            <MetricCard label="Invalid" value={q.invalid_reviews} accent="text-accent-rose" />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <GlassCard className="p-5">
              <h3 className="mb-1 text-sm font-medium text-slate-200">Quality score</h3>
              <QualityGauge score={q.quality_score} label={q.dataset_decision} />
              <div className="mt-3 flex items-center justify-center">
                <StatusBadge status={q.dataset_decision} />
              </div>
            </GlassCard>

            <GlassCard className="p-5 lg:col-span-2">
              <h3 className="mb-2 text-sm font-medium text-slate-200">Component breakdown</h3>
              <QualityRadar
                scores={[
                  { dimension: "Review Detection", score: q.component_scores.review_detection },
                  { dimension: "Opinion Density", score: q.component_scores.opinion_density },
                  { dimension: "Feature Density", score: q.component_scores.feature_density },
                  { dimension: "Avg Length", score: q.component_scores.average_length },
                  { dimension: "Language Quality", score: q.component_scores.language_quality },
                  { dimension: "Diversity", score: q.component_scores.dataset_diversity },
                ]}
              />
            </GlassCard>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <GlassCard className="p-5">
              <h3 className="mb-3 text-sm font-medium text-slate-200">Dataset metrics</h3>
              <dl className="space-y-2 text-sm">
                {[
                  ["Average length", `${q.average_word_count} words`],
                  ["Opinion density", `${(q.opinion_density * 100).toFixed(0)}%`],
                  ["Feature density", `${(q.feature_density * 100).toFixed(0)}%`],
                  ["Alphabetic ratio", q.alphabetic_ratio.toFixed(2)],
                  ["Gibberish ratio", `${(q.gibberish_ratio * 100).toFixed(0)}%`],
                  ["Excessive symbols", `${(q.excessive_symbol_ratio * 100).toFixed(0)}%`],
                  ["Dataset diversity", q.dataset_diversity.toFixed(2)],
                  ["Exact duplicates", String(q.exact_duplicates)],
                  ["Near-duplicates", String(q.near_duplicates)],
                ].map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between border-b border-white/5 pb-1.5">
                    <dt className="text-slate-400">{k}</dt>
                    <dd className="font-mono text-slate-300">{v}</dd>
                  </div>
                ))}
              </dl>
            </GlassCard>

            <GlassCard className="p-5">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
                <CheckCircle2 size={15} className="text-accent-emerald" /> Decision reasons
              </h3>
              <ul className="space-y-2 text-sm text-slate-300">
                {q.reasons.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 rounded-xl bg-white/[0.03] p-2.5">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-cyan" />
                    {r}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[11px] text-slate-600">
                Weights: review detection 25% · Opinion density 15% · Feature density 10% · Average length 15% · Language quality 20% · Dataset diversity 15% — minus duplicate &amp; uncertainty penalties.
              </p>
            </GlassCard>
          </div>
        </div>
      )}
    </AppShell>
  );
}
