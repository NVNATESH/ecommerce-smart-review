"use client";

import Link from "next/link";
import { useState } from "react";
import { ShieldAlert } from "lucide-react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useAnalysis } from "@/hooks/useAnalysis";
import {
  EmptyState,
  ErrorState,
  GlassCard,
  MetricCard,
  Skeleton,
} from "@/components/ui/primitives";
import { ReviewTable } from "@/components/reviews/ReviewTable";

export default function SuspiciousPage() {
  const { summary, loading, error } = useAnalysis();
  const [suspiciousOnly, setSuspiciousOnly] = useState(true);

  if (!summary && !loading && !error) {
    return (
      <AppShell>
        <PageHeader title="Suspicious Reviews" />
        <EmptyState
          title="No analysis yet"
          description="Run an analysis first. Heuristic signals surface potentially manipulated reviews — never proof of fraud."
          action={<Link href="/analysis" className="rounded-xl bg-accent-blue/20 border border-accent-blue/30 px-5 py-2.5 text-sm text-accent-cyan">Analyze Reviews</Link>}
        />
      </AppShell>
    );
  }

  const stats = summary?.statistics;
  const suspiciousRate = stats && stats.reviews_analyzed > 0
    ? ((stats.suspicious_reviews / stats.reviews_analyzed) * 100).toFixed(1)
    : "0";

  return (
    <AppShell>
      <PageHeader
        title="Suspicious Reviews"
        subtitle="Heuristic signals — reported as 'suspicious', never as proven fake."
      />

      {loading && <Skeleton className="h-64 w-full" />}
      {error && <ErrorState message={error} />}

      {summary && stats && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <MetricCard label="Suspicious Count" value={stats.suspicious_reviews} icon={<ShieldAlert size={18} />} accent="text-accent-amber" />
            <MetricCard label="Suspicious Rate" value={`${suspiciousRate}%`} />
            <MetricCard label="Reviews Analyzed" value={stats.reviews_analyzed} />
          </div>

          <GlassCard className="p-5">
            <h3 className="mb-4 text-sm font-medium text-slate-200">View</h3>
            <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={suspiciousOnly}
                onChange={(e) => setSuspiciousOnly(e.target.checked)}
                className="rounded border-white/20 bg-white/5"
              />
              Suspicious only
            </label>
          </GlassCard>

          <GlassCard className="p-5">
            {summary.analysis_id && (
              <ReviewTable
                analysisId={summary.analysis_id}
                filters={{
                  suspicious: suspiciousOnly || undefined,
                  sort: "suspicion_score",
                  order: "desc",
                }}
                showFilters={false}
                pageSize={20}
              />
            )}
          </GlassCard>

          <GlassCard className="p-4">
            <p className="text-[11px] leading-relaxed text-slate-600">
              Suspicion scores are heuristic indicators (all-caps shouting, repeated words, promotional
              language, duplicates…). A high score does not prove a review is fake, and a low score does not
              prove it is genuine. Use these signals alongside the full review context.
            </p>
          </GlassCard>
        </div>
      )}
    </AppShell>
  );
}
