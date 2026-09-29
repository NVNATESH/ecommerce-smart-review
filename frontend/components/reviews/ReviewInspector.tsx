"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Copy, X } from "lucide-react";
import type { ReviewResult } from "@/lib/types";
import {
  ConfidenceBadge,
  GlassCard,
  SentimentBadge,
  StatusBadge,
} from "@/components/ui/primitives";

export function ReviewInspector({
  review,
  onClose,
}: {
  review: ReviewResult;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`Review inspector: review ${review.id}`}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <GlassCard className="p-6">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-500">Review Inspector</p>
              <h2 className="mt-1 text-lg font-medium text-slate-100">Review #{review.id}</h2>
            </div>
            <button
              onClick={onClose}
              aria-label="Close inspector"
              className="rounded-lg p-2 text-slate-400 transition hover:bg-white/10 hover:text-slate-200"
            >
              <X size={18} />
            </button>
          </div>

          <blockquote className="rounded-xl border border-white/10 bg-black/20 p-4 text-sm leading-relaxed text-slate-300">
            &ldquo;{review.original_text}&rdquo;
          </blockquote>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <InspectorRow label="Review Status">
              <StatusBadge status={review.review_status} />
              <span className="ml-2 font-mono text-xs text-slate-500">
                {(review.review_probability * 100).toFixed(1)}% review
              </span>
            </InspectorRow>
            <InspectorRow label="Product Relevance">
              <StatusBadge status={review.relevance_level} />
              <span className="ml-2 font-mono text-xs text-slate-500">
                {(review.relevance * 100).toFixed(0)}
              </span>
            </InspectorRow>
            <InspectorRow label="Sentiment">
              <SentimentBadge sentiment={review.sentiment} />
            </InspectorRow>
            <InspectorRow label="Confidence">
              <ConfidenceBadge confidence={review.confidence} />
              <span className="ml-1 text-[10px] text-slate-600">model certainty</span>
            </InspectorRow>
          </div>

          <div className="mt-4">
            <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Class probabilities</p>
            <div className="space-y-1.5">
              {[
                { label: "Positive", value: review.positive_probability, color: "bg-emerald-400" },
                { label: "Negative", value: review.negative_probability, color: "bg-rose-400" },
                { label: "Neutral", value: review.neutral_probability, color: "bg-slate-400" },
              ].map((p) => (
                <div key={p.label} className="flex items-center gap-3 text-xs">
                  <span className="w-16 text-slate-400">{p.label}</span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                    <div className={`h-full rounded-full ${p.color}`} style={{ width: `${p.value * 100}%` }} />
                  </div>
                  <span className="w-12 text-right font-mono text-slate-400">{(p.value * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>

          {review.aspects.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Detected aspects</p>
              <div className="flex flex-wrap gap-2">
                {review.aspects.map((a, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-xs">
                    {a.category}: <SentimentBadge sentiment={a.sentiment} />
                    <span className="font-mono text-slate-500">{(a.confidence * 100).toFixed(0)}%</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {(review.suspicious || review.suspicion_score > 0) && (
            <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
              <p className="flex items-center gap-2 text-xs font-medium text-amber-300">
                <AlertTriangle size={13} />
                Suspicion score {review.suspicion_score}/100 {review.suspicious ? "— flagged suspicious" : ""}
              </p>
              {review.suspicion_reasons.length > 0 && (
                <ul className="mt-1.5 list-inside list-disc text-xs text-slate-400">
                  {review.suspicion_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {(review.duplicate || review.near_duplicate) && (
            <p className="mt-3 flex items-center gap-2 text-xs text-slate-400">
              <Copy size={13} />
              {review.duplicate ? "Exact duplicate" : "Near-duplicate"} of review #{review.duplicate_of}
            </p>
          )}

          {review.contributing_terms.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">
                Contributing model features
              </p>
              <div className="flex flex-wrap gap-2">
                {review.contributing_terms.map((t) => (
                  <span key={t} className="rounded-lg bg-accent-blue/10 px-2 py-1 font-mono text-xs text-accent-cyan">
                    {t}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-[11px] text-slate-600">
                These model features contributed strongly to the classification. This is a model
                attribution view, not a causal explanation.
              </p>
            </div>
          )}
        </GlassCard>
      </motion.div>
    </div>
  );
}

function InspectorRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.03] p-3">
      <p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p>
      <div className="mt-1.5 flex items-center">{children}</div>
    </div>
  );
}
