"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  Gauge,
  Smile,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  XCircle,
} from "lucide-react";
import { useAnalysisStore } from "@/lib/store";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import {
  EmptyState,
  ErrorState,
  GlassCard,
  MetricCard,
  Skeleton,
  StatusBadge,
} from "@/components/ui/primitives";
import { ConfidenceHistogramChart, QualityGauge, SentimentPie } from "@/components/charts/Charts";
import Link from "next/link";

export default function DashboardPage() {
  const { analysisId, summary, loading, error, loadSummary } = useAnalysisStore();
  const router = useRouter();

  useEffect(() => {
    const id = analysisId ?? sessionStorage.getItem("analysisId");
    if (id) {
      if (!summary || summary.analysis_id !== id) loadSummary(id);
    }
  }, [analysisId, summary, loadSummary]);

  if (!analysisId && !loading && !summary) {
    return (
      <AppShell>
        <PageHeader title="Dashboard" subtitle="Transform customer reviews into explainable product intelligence." />
        <EmptyState
          title="No analysis yet"
          description="Paste reviews or upload a CSV to generate sentiment, aspect intelligence and dataset quality reports."
          action={
            <Link
              href="/analysis"
              className="rounded-xl bg-gradient-to-r from-accent-blue to-accent-violet px-5 py-2.5 text-sm font-medium text-white shadow-glow transition hover:opacity-90"
            >
              Analyze Reviews
            </Link>
          }
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title="Dashboard"
        subtitle={summary ? `Analysis ${summary.analysis_id.slice(0, 8)} · ${summary.source === "csv" ? `CSV upload${summary.filename ? `: ${summary.filename}` : ""}` : "pasted text"}` : "Loading analysis…"}
      />

      {(loading || (!summary && !error)) && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      )}
      {error && <ErrorState message={error} />}

      {summary && (
        <div className="space-y-6">
          {/* Metric cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <MetricCard label="Reviews Analyzed" value={summary.statistics.reviews_analyzed} icon={<Activity size={18} />} delay={0} />
            <MetricCard label="Dataset Quality" value={summary.quality.quality_score.toFixed(0)} sub={summary.quality.dataset_decision} icon={<BadgeCheck size={18} />} accent={summary.quality.quality_score >= 80 ? "text-accent-emerald" : summary.quality.quality_score >= 60 ? "text-accent-amber" : "text-accent-rose"} delay={0.05} />
            <MetricCard label="Avg Confidence" value={`${(summary.statistics.average_confidence * 100).toFixed(0)}%`} sub="model + aspect evidence" icon={<Gauge size={18} />} delay={0.1} />
            <MetricCard label="Positive" value={summary.sentiment.positive_percentage.toFixed(0) + "%"} sub={`${summary.sentiment.positive} reviews`} icon={<Smile size={18} />} accent="text-accent-emerald" delay={0.15} />
            <MetricCard label="Negative" value={summary.sentiment.negative_percentage.toFixed(0) + "%"} sub={`${summary.sentiment.negative} reviews`} icon={<ThumbsDown size={18} />} accent="text-accent-rose" delay={0.2} />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Sentiment distribution */}
            <GlassCard className="p-5">
              <h3 className="mb-2 text-sm font-medium text-slate-200">Sentiment distribution</h3>
              <SentimentPie
                data={[
                  { name: "Positive", value: summary.sentiment.positive },
                  { name: "Neutral", value: summary.sentiment.neutral },
                  { name: "Negative", value: summary.sentiment.negative },
                  ...(summary.sentiment.mixed ? [{ name: "Mixed", value: summary.sentiment.mixed }] : []),
                ]}
              />
              <div className="mt-2 flex items-center justify-between rounded-xl bg-white/[0.03] px-3 py-2 text-sm">
                <span className="text-slate-400">Overall verdict</span>
                <span className="font-medium text-accent-cyan">{summary.verdict.overall_sentiment}</span>
              </div>
            </GlassCard>

            {/* Quality gauge + counts */}
            <GlassCard className="p-5">
              <h3 className="mb-1 text-sm font-medium text-slate-200">Dataset quality</h3>
              <QualityGauge score={summary.quality.quality_score} label={summary.quality.dataset_decision} />
              <div className="mt-2 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-xl bg-white/[0.03] p-2">
                  <p className="flex items-center justify-center gap-1 text-emerald-400"><BadgeCheck size={12} /> {summary.quality.valid_reviews}</p>
                  <p className="text-slate-600">valid</p>
                </div>
                <div className="rounded-xl bg-white/[0.03] p-2">
                  <p className="flex items-center justify-center gap-1 text-amber-400"><AlertTriangle size={12} /> {summary.quality.uncertain_reviews}</p>
                  <p className="text-slate-600">uncertain</p>
                </div>
                <div className="rounded-xl bg-white/[0.03] p-2">
                  <p className="flex items-center justify-center gap-1 text-rose-400"><XCircle size={12} /> {summary.quality.invalid_reviews}</p>
                  <p className="text-slate-600">invalid</p>
                </div>
              </div>
              <div className="mt-2 flex justify-between text-xs text-slate-500">
                <span>Duplicates removed: <span className="text-slate-300">{summary.quality.exact_duplicates}</span></span>
                <span>Near-duplicates: <span className="text-slate-300">{summary.quality.near_duplicates}</span></span>
              </div>
            </GlassCard>

            {/* Confidence histogram */}
            <GlassCard className="p-5">
              <h3 className="mb-2 text-sm font-medium text-slate-200">Prediction confidence</h3>
              <ConfidenceHistogramChart
                buckets={summary.confidence_histogram.buckets}
                counts={summary.confidence_histogram.counts}
              />
              <p className="text-[11px] text-slate-600">
                Confidence reflects model certainty for the predicted class — not a guarantee of correctness.
              </p>
            </GlassCard>
          </div>

          {/* Verdict */}
          <GlassCard className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-slate-200">Product-level verdict</h3>
              <StatusBadge status={summary.quality.dataset_decision} />
            </div>
            <p className="text-sm leading-relaxed text-slate-300">{summary.verdict.statement}</p>
            <p className="mt-2 text-[11px] text-slate-600">
              Factual summary from transparent aggregation rules — not an unconditional buy/don&apos;t-buy recommendation.
            </p>
          </GlassCard>

          <div className="grid gap-6 lg:grid-cols-3">
            <ProsConsCard title="Pros" icon={<ThumbsUp size={15} className="text-emerald-400" />} items={summary.pros} positive />
            <ProsConsCard title="Cons" icon={<ThumbsDown size={15} className="text-rose-400" />} items={summary.cons} />
            <GlassCard className="p-5">
              <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
                <Sparkles size={15} className="text-accent-cyan" /> Most discussed features
              </h3>
              <ul className="space-y-2">
                {summary.most_discussed.slice(0, 6).map((a) => (
                  <li key={a.aspect} className="flex items-center justify-between text-sm">
                    <span className="text-slate-300">{a.aspect}</span>
                    <span className="font-mono text-xs text-slate-500">{a.mention_count} mentions</span>
                  </li>
                ))}
                {summary.most_discussed.length === 0 && <li className="text-sm text-slate-500">No aspects detected.</li>}
              </ul>
            </GlassCard>
          </div>
        </div>
      )}
    </AppShell>
  );
}

function ProsConsCard({
  title,
  icon,
  items,
  positive = false,
}: {
  title: string;
  icon: React.ReactNode;
  items: { aspect: string; percentage: number; mention_count: number }[];
  positive?: boolean;
}) {
  return (
    <GlassCard className="p-5">
      <h3 className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-200">{icon} {title}</h3>
      <p className="mb-3 text-[11px] text-slate-600">
        All aspects that lean {positive ? "positive" : "negative"}, strongest first.
      </p>
      <ul className="space-y-2.5">
        {items.map((item) => (
          <li key={item.aspect}>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-300">{item.aspect}</span>
              <span className="font-mono text-[11px] text-slate-500">
                {item.mention_count} mention{item.mention_count === 1 ? "" : "s"}
              </span>
            </div>
            <div className="mt-1 h-1 overflow-hidden rounded-full bg-white/5">
              <div
                className={`h-full rounded-full ${positive ? "bg-emerald-400" : "bg-rose-400"}`}
                style={{ width: `${item.percentage}%` }}
              />
            </div>
          </li>
        ))}
        {items.length === 0 && <li className="text-sm text-slate-500">No aspect leans this way yet.</li>}
      </ul>
    </GlassCard>
  );
}
