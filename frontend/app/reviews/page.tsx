"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useAnalysis } from "@/hooks/useAnalysis";
import { EmptyState, ErrorState, GlassCard, Skeleton } from "@/components/ui/primitives";
import { ReviewInspector } from "@/components/reviews/ReviewInspector";
import { ReviewTable } from "@/components/reviews/ReviewTable";
import type { ReviewResult } from "@/lib/types";

export default function ReviewsPage() {
  const { summary, loading, error } = useAnalysis();
  const [selected, setSelected] = useState<ReviewResult | null>(null);

  if (!summary && !loading && !error) {
    return (
      <AppShell>
        <PageHeader title="Review Inspector" />
        <EmptyState
          title="No analysis yet"
          description="Run an analysis first, then click any review to inspect its full prediction details."
          action={<Link href="/analysis" className="rounded-xl bg-accent-blue/20 border border-accent-blue/30 px-5 py-2.5 text-sm text-accent-cyan">Analyze Reviews</Link>}
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title="Review Inspector"
        subtitle="Data explorer — click a row for the full prediction breakdown."
      />

      {loading && <Skeleton className="h-64 w-full" />}
      {error && <ErrorState message={error} />}

      {summary && (
        <GlassCard className="p-5">
          <ReviewTable
            analysisId={summary.analysis_id}
            pageSize={25}
            onSelect={setSelected}
          />
        </GlassCard>
      )}

      {selected && <ReviewInspector review={selected} onClose={() => setSelected(null)} />}
    </AppShell>
  );
}
