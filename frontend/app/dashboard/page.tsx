"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  FolderOpen,
  BadgeCheck,
  Gauge,
  MessageCircleQuestion,
  ShieldCheck,
  Smile,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  XCircle,
} from "lucide-react";
import { useAnalysisStore } from "@/lib/store";
import type { ProductListItem } from "@/lib/types";
import { AppShell, PageHeader } from "@/components/layout/AppShell";
import {
  EmptyState,
  ErrorState,
  GlassCard,
  MetricCard,
  Skeleton,
  StatusBadge,
} from "@/components/ui/primitives";
import {
  ConfidenceHistogramChart,
  EmotionRadar,
  QualityGauge,
  SentimentPie,
} from "@/components/charts/Charts";
import { askReview, listProducts } from "@/lib/api";
import Link from "next/link";

function AskCard({ analysisId }: { analysisId: string }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<{ answer: string; matched: number; quotes: { id: number; text: string; sentiment: string }[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async () => {
    if (!question.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const r = await askReview(analysisId, question.trim());
      setResult(r);
    } catch {
      setError("Could not answer right now — is the backend running?");
    } finally {
      setBusy(false);
    }
  }, [analysisId, question, busy]);

  return (
    <GlassCard className="p-5">
      <h3 className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-200">
        <MessageCircleQuestion size={15} className="text-accent-cyan" /> Ask the Reviews
      </h3>
      <p className="mb-3 text-[11px] text-slate-600">
        Ask anything about the analysed reviews — answered with real quotes as evidence.
      </p>
      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="e.g. how is the camera? any delivery issues?"
          aria-label="Ask the reviews"
          className="flex-1 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-accent-blue/50 focus:outline-none"
        />
        <button
          onClick={submit}
          disabled={busy || !question.trim()}
          className="rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-40"
        >
          {busy ? "…" : "Ask"}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-rose-400">{error}</p>}
      {result && (
        <div className="mt-3 rounded-xl border border-sky-400/20 bg-sky-400/5 p-3">
          <p className="text-sm text-slate-200">{result.answer}</p>
          {result.quotes.length > 0 && (
            <ul className="mt-2 space-y-1">
              {result.quotes.map((q) => (
                <li key={q.id} className="text-xs text-slate-400">
                  &ldquo;{q.text}&rdquo; <span className="text-slate-600">— review #{q.id} ({q.sentiment})</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </GlassCard>
  );
}

function TrustCard({ trust }: { trust: NonNullable<import("@/lib/types").AnalysisSummary["trust"]> }) {
  const bandColor =
    trust.band === "High confidence" ? "text-accent-emerald" : trust.band === "Moderate confidence" ? "text-accent-amber" : "text-accent-rose";
  return (
    <GlassCard className="p-5">
      <h3 className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-200">
        <ShieldCheck size={15} className="text-accent-emerald" /> Review Trust Score
      </h3>
      <p className="mb-2 text-[11px] text-slate-600">How much this dataset&apos;s verdict can be trusted.</p>
      <p className={`text-4xl font-semibold ${bandColor}`}>{trust.score.toFixed(0)}</p>
      <p className={`text-xs ${bandColor}`}>{trust.band}</p>
      <div className="mt-3 space-y-1.5">
        {[
          ["Valid reviews", trust.components.validReviewPct],
          ["Suspicious reviews", trust.components.suspiciousPct],
          ["Duplicate reviews", trust.components.duplicatePct],
          ["Review volume", trust.components.volumeScore],
        ].map(([label, val]) => (
          <div key={label as string} className="flex items-center justify-between text-xs">
            <span className="text-slate-500">{label}</span>
            <span className="font-mono text-slate-400">{Number(val).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

function EmotionCard({ emotions }: { emotions: NonNullable<import("@/lib/types").AnalysisSummary["emotions"]> }) {
  return (
    <GlassCard className="p-5">
      <h3 className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-200">
        <Smile size={15} className="text-accent-amber" /> Emotion Mix
      </h3>
      <p className="mb-2 text-[11px] text-slate-600">Lexicon-based emotion signals across reviews.</p>
      <EmotionRadar data={emotions} />
    </GlassCard>
  );
}

export default function DashboardPage() {
  const { analysisId, productName, summary, loading, error, notFound, loadSummary, setAnalysis, reset } = useAnalysisStore();
  const router = useRouter();
  const [products, setProducts] = useState<ProductListItem[] | null>(null);

  const loadProducts = useCallback(async () => {
    try {
      const res = await listProducts();
      setProducts(res.products);
    } catch {
      setProducts([]);
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    const id = analysisId ?? sessionStorage.getItem("analysisId");
    if (id && (!summary || summary.analysis_id !== id)) loadSummary(id);
  }, [analysisId, summary, loadSummary]);

  const selectedProduct =
    products?.find((p) => p.id === analysisId || p.analysis_id === analysisId) ?? null;

  const openProduct = (p: ProductListItem) => {
    if (!p.analysis_id) return;
    sessionStorage.setItem("analysisId", p.analysis_id);
    setAnalysis(p.analysis_id, null, p.name);
  };
  const backToAll = () => {
    reset();
    sessionStorage.removeItem("analysisId");
  };

  const aggregates = (() => {
    if (!products || products.length === 0) return null;
    const totalReviews = products.reduce((a, p) => a + p.review_count, 0);
    const trusted = products.filter((p) => p.trust !== null && p.trust !== undefined);
    const qualified = products.filter((p) => p.quality !== null && p.quality !== undefined);
    return {
      count: products.length,
      totalReviews,
      avgTrust: trusted.length ? trusted.reduce((a, p) => a + (p.trust ?? 0), 0) / trusted.length : 0,
      avgQuality: qualified.length ? qualified.reduce((a, p) => a + (p.quality ?? 0), 0) / qualified.length : 0,
    };
  })();

  const hasSelection = Boolean(analysisId || summary);

  return (
    <AppShell>
      <PageHeader
        title="Dashboard"
        subtitle={
          selectedProduct
            ? `${selectedProduct.name} — analysis detail`
            : summary
              ? `Analysis ${summary.analysis_id.slice(0, 8)} · ${summary.source === "csv" ? `CSV upload${summary.filename ? `: ${summary.filename}` : ""}` : "pasted text"}`
              : "All stored products at a glance"
        }
        right={
          hasSelection ? (
            <button
              onClick={backToAll}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-slate-300 transition hover:bg-white/10"
            >
              ← All products
            </button>
          ) : undefined
        }
      />

      {/* ---- All-products overview (always visible) ---- */}
      {aggregates && (
        <div className="mb-8 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Stored Products" value={aggregates.count} icon={<FolderOpen size={18} />} />
            <MetricCard label="Total Reviews" value={aggregates.totalReviews} icon={<Activity size={18} />} />
            <MetricCard label="Avg Trust" value={aggregates.avgTrust.toFixed(0)} icon={<ShieldCheck size={18} />} accent="text-accent-emerald" />
            <MetricCard label="Avg Quality" value={aggregates.avgQuality.toFixed(0)} icon={<BadgeCheck size={18} />} accent="text-accent-cyan" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {products?.map((p) => (
              <GlassCard key={p.id} className={`p-4 ${selectedProduct?.id === p.id ? "border-sky-400/50" : ""}`}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-slate-100">{p.name}</p>
                    <p className="mt-0.5 text-[11px] text-slate-500">{p.review_count} reviews</p>
                  </div>
                  {p.verdict && <StatusBadge status={p.verdict} />}
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between"><span className="text-slate-500">Trust</span><span className="font-mono text-emerald-300">{p.trust?.toFixed(0) ?? "—"}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Quality</span><span className="font-mono text-sky-300">{p.quality?.toFixed(0) ?? "—"}</span></div>
                </div>
                {p.analysis_id ? (
                  <button
                    onClick={() => openProduct(p)}
                    className="mt-3 w-full rounded-xl border border-sky-400/30 bg-sky-400/10 px-3 py-2 text-xs font-medium text-sky-200 transition hover:bg-sky-400/20"
                  >
                    Open analysis
                  </button>
                ) : (
                  <p className="mt-3 text-center text-[11px] text-slate-600">Analysis in progress…</p>
                )}
              </GlassCard>
            ))}
          </div>
        </div>
      )}

      {/* ---- Selected analysis detail ---- */}
      {(loading || (!summary && hasSelection)) && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      )}
      {error && !notFound && <ErrorState message={error} />}
      {notFound && (
        <GlassCard className="mb-6 border-amber-400/20 p-4">
          <p className="text-xs text-amber-300">
            That analysis is no longer in memory (server restarted). Pick a product above or start a new analysis.
          </p>
        </GlassCard>
      )}

      {summary && (
        <div className="space-y-6">
          {selectedProduct && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <BadgeCheck size={13} className="text-accent-cyan" />
              Showing analysis for <span className="font-medium text-slate-300">{selectedProduct.name}</span>
            </div>
          )}

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

          {/* Trust score + emotion mix */}
          <div className="grid gap-6 lg:grid-cols-2">
            {summary.trust && <TrustCard trust={summary.trust} />}
            {summary.emotions && summary.emotions.length > 0 && <EmotionCard emotions={summary.emotions} />}
          </div>

          {/* Ask the Reviews */}
          <AskCard analysisId={summary.analysis_id} />

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

      {!hasSelection && products && products.length > 0 && (
        <GlassCard className="p-6 text-center">
          <p className="text-sm text-slate-400">
            Select a product above to open its full analysis — or analyze new reviews to create one.
          </p>
          <Link
            href="/analysis"
            className="mt-4 inline-block rounded-xl bg-gradient-to-r from-accent-blue to-accent-violet px-5 py-2.5 text-sm font-medium text-white shadow-glow transition hover:opacity-90"
          >
            Analyze Reviews
          </Link>
        </GlassCard>
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
  items: { aspect: string; percentage: number; mention_count: number; quotes: string[] }[];
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
            {item.quotes.length > 0 && (
              <ul className="mt-1.5 space-y-1">
                {item.quotes.map((q, qi) => (
                  <li key={qi} className="text-[11px] leading-snug text-slate-500">
                    {q}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
        {items.length === 0 && <li className="text-sm text-slate-500">No aspect leans this way yet.</li>}
      </ul>
    </GlassCard>
  );
}
