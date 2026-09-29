"use client";

import Link from "next/link";
import { Download, FileJson, FileSpreadsheet, FileText } from "lucide-react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useAnalysis } from "@/hooks/useAnalysis";
import { exportUrl } from "@/lib/api";
import { EmptyState, ErrorState, GlassCard, Skeleton } from "@/components/ui/primitives";

const FORMATS = [
  { format: "reviews_csv", label: "Processed Reviews", ext: "CSV", icon: FileSpreadsheet, desc: "Every review with status, sentiment, confidence, suspicion and aspect flags." },
  { format: "aspects_csv", label: "Aspect Summary", ext: "CSV", icon: FileSpreadsheet, desc: "Mention counts and sentiment percentages per aspect." },
  { format: "quality_json", label: "Quality Report", ext: "JSON", icon: FileJson, desc: "Quality components, decision and reasons." },
  { format: "metrics_json", label: "Model Metrics", ext: "JSON", icon: FileJson, desc: "Training evaluation metrics for both models." },
  { format: "analysis_json", label: "Complete Analysis", ext: "JSON", icon: FileText, desc: "The full result: summary, quality, aspects and all reviews." },
];

export default function ExportsPage() {
  const { summary, loading, error } = useAnalysis();

  if (!summary && !loading && !error) {
    return (
      <AppShell>
        <PageHeader title="Exports" />
        <EmptyState
          title="No analysis yet"
          description="Run an analysis first, then download its results here."
          action={<Link href="/analysis" className="rounded-xl bg-accent-blue/20 border border-accent-blue/30 px-5 py-2.5 text-sm text-accent-cyan">Analyze Reviews</Link>}
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        title="Exports"
        subtitle="CSV exports are sanitized against spreadsheet formula injection."
      />

      {loading && <Skeleton className="h-64 w-full" />}
      {error && <ErrorState message={error} />}

      {summary && (
        <div className="grid gap-4 md:grid-cols-2">
          {FORMATS.map(({ format, label, ext, icon: Icon, desc }) => (
            <a
              key={format}
              href={exportUrl(summary.analysis_id, format)}
              className="glass glass-hover group flex items-start gap-4 p-5"
            >
              <div className="rounded-xl bg-accent-blue/10 p-3 text-accent-cyan">
                <Icon size={20} />
              </div>
              <div className="flex-1">
                <p className="flex items-center gap-2 font-medium text-slate-200">
                  {label}
                  <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] font-mono text-slate-500">{ext}</span>
                </p>
                <p className="mt-1 text-xs leading-relaxed text-slate-500">{desc}</p>
              </div>
              <Download size={16} className="mt-1 text-slate-600 transition group-hover:text-accent-cyan" />
            </a>
          ))}
        </div>
      )}
    </AppShell>
  );
}
