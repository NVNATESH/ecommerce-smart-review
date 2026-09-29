"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Cpu, ShieldCheck } from "lucide-react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { useAnalysis } from "@/hooks/useAnalysis";
import { getModels } from "@/lib/api";
import type { ModelInfo } from "@/lib/types";
import {
  EmptyState,
  ErrorState,
  GlassCard,
  Skeleton,
} from "@/components/ui/primitives";
import { SentimentBar } from "@/components/charts/Charts";

export default function ModelsPage() {
  const { summary } = useAnalysis();
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ message: string; code?: string } | null>(null);

  useEffect(() => {
    getModels()
      .then((res) => setModels(res.models))
      .catch((e) => setError({ message: e.message, code: e.code }))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <PageHeader
        title="Model Performance"
        subtitle="Candidates compared on MACRO F1 — the primary selection metric."
      />

      {loading && <Skeleton className="h-64 w-full" />}
      {error && <ErrorState message={error.message} code={error.code} />}

      {!loading && !error && models.length === 0 && (
        <EmptyState
          title="Models not trained"
          description="Run python training/train_sentiment.py and python training/train_review_detector.py, then restart the backend."
        />
      )}

      <div className="space-y-6">
        {models.map((m) => {
          const selected = m.candidates.find((c) => c.model_name === m.selected_model);
          return (
            <GlassCard key={m.task} className="p-5">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="flex items-center gap-2 text-sm font-medium text-slate-200">
                    {m.task === "sentiment" ? <Cpu size={15} className="text-accent-cyan" /> : <ShieldCheck size={15} className="text-accent-violet" />}
                    {m.task === "sentiment" ? "Sentiment Classifier" : "Review Detector"}
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    {m.dataset_name && <span className="text-slate-400">{m.dataset_name} · {m.dataset_size?.toLocaleString()} cleaned rows · </span>}
                    {m.training_rows.toLocaleString()} training · {m.validation_rows ? `${m.validation_rows.toLocaleString()} validation · ` : ""}
                    {m.test_rows.toLocaleString()} test rows · trained {m.trained_at.slice(0, 10)}
                  </p>
                  {m.class_distribution && (
                    <p className="mt-0.5 text-[11px] text-slate-600">
                      Class distribution: {Object.entries(m.class_distribution).map(([k, v]) => `${k} ${v.toLocaleString()}`).join(" · ")}
                    </p>
                  )}
                  {m.imbalance_handling && (
                    <p className="mt-0.5 text-[11px] text-slate-600">Imbalance handling: {m.imbalance_handling}</p>
                  )}
                </div>
                <span className="rounded-full border border-accent-cyan/30 bg-accent-cyan/10 px-3 py-1 text-xs font-medium text-accent-cyan">
                  Selected: {m.selected_model}
                </span>
              </div>

              <div className="grid gap-6 lg:grid-cols-2">
                {/* Comparison chart (validation set) */}
                <div>
                  <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">
                    Candidate comparison — validation set (selection metric: {m.selection_metric})
                  </p>
                  <SentimentBar
                    data={m.candidates.map((c) => ({
                      model: c.model_name.replace(" (Calibrated)", ""),
                      "Macro F1": c.macro_f1,
                      Accuracy: c.accuracy,
                    }))}
                    xKey="model"
                    bars={[
                      { key: "Macro F1", color: "#22D3EE" },
                      { key: "Accuracy", color: "#8B5CF6" },
                    ]}
                    height={240}
                  />
                </div>

                {/* Metrics of selected model */}
                <div>
                  {m.selected_model_test_metrics ? (
                    <>
                      <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">
                        Final held-out test performance ({m.selected_model_test_metrics.model_name})
                      </p>
                      <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                        {[
                          ["Accuracy", m.selected_model_test_metrics.accuracy],
                          ["Precision (macro)", m.selected_model_test_metrics.precision_macro],
                          ["Recall (macro)", m.selected_model_test_metrics.recall_macro],
                          ["Macro F1", m.selected_model_test_metrics.macro_f1],
                          ["Weighted F1", m.selected_model_test_metrics.weighted_f1],
                        ].map(([k, v]) => (
                          <div key={k as string} className="rounded-xl bg-white/[0.03] p-3">
                            <dt className="text-[11px] text-slate-500">{k}</dt>
                            <dd className="mt-1 font-mono text-lg text-accent-cyan">{((v as number) * 100).toFixed(1)}%</dd>
                          </div>
                        ))}
                      </dl>
                      {m.selected_model_test_metrics.confusion_matrix.length > 0 && (
                        <div className="mt-4">
                          <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Confusion matrix — test set (rows = true, cols = predicted)</p>
                          <div className="inline-block">
                            <table className="text-xs">
                              <thead>
                                <tr>
                                  <th className="p-1" />
                                  {m.classes.map((c) => (
                                    <th key={c} className="p-1 text-slate-500">{c.slice(0, 3)}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {m.selected_model_test_metrics.confusion_matrix.map((row, i) => (
                                  <tr key={i}>
                                    <td className="p-1 text-slate-500">{m.classes[i]}</td>
                                    {row.map((v, j) => (
                                      <td key={j} className="p-1">
                                        <span
                                          className={`inline-flex h-8 w-10 items-center justify-center rounded font-mono ${
                                            i === j ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/15 text-rose-300"
                                          }`}
                                        >
                                          {v}
                                        </span>
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Selected model metrics</p>
                      {selected && (
                        <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                          {[
                            ["Accuracy", selected.accuracy],
                            ["Precision (macro)", selected.precision_macro],
                            ["Recall (macro)", selected.recall_macro],
                            ["Macro F1", selected.macro_f1],
                            ["Weighted F1", selected.weighted_f1],
                          ].map(([k, v]) => (
                            <div key={k as string} className="rounded-xl bg-white/[0.03] p-3">
                              <dt className="text-[11px] text-slate-500">{k}</dt>
                              <dd className="mt-1 font-mono text-lg text-accent-cyan">{((v as number) * 100).toFixed(1)}%</dd>
                            </div>
                          ))}
                        </dl>
                      )}
                      {selected && selected.confusion_matrix.length > 0 && (
                        <div className="mt-4">
                          <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Confusion matrix (rows = true, cols = predicted)</p>
                          <div className="inline-block">
                            <table className="text-xs">
                              <thead>
                                <tr>
                                  <th className="p-1" />
                                  {m.classes.map((c) => (
                                    <th key={c} className="p-1 text-slate-500">{c.slice(0, 3)}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {selected.confusion_matrix.map((row, i) => (
                                  <tr key={i}>
                                    <td className="p-1 text-slate-500">{m.classes[i]}</td>
                                    {row.map((v, j) => (
                                      <td key={j} className="p-1">
                                        <span
                                          className={`inline-flex h-8 w-10 items-center justify-center rounded font-mono ${
                                            i === j ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/15 text-rose-300"
                                          }`}
                                        >
                                          {v}
                                        </span>
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              <p className="mt-4 text-[11px] text-slate-600">
                Training data: {m.training_dataset} · TF-IDF {JSON.stringify(m.tfidf_config)} · selected by {m.selection_metric}.
                {m.task === "sentiment" && " Probabilities are model certainties, not guarantees of correctness."}
              </p>
            </GlassCard>
          );
        })}
      </div>
    </AppShell>
  );
}
