"use client";

import { motion } from "framer-motion";
import { ArrowRight, BarChart3, ShieldCheck, Sparkles } from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useState } from "react";
import type { AnalysisResponse } from "@/lib/types";
import { SentimentBadge } from "@/components/ui/primitives";
import { Scene3DBoundary } from "@/components/3d/Scene3DBoundary";

// The chosen hero design: the neural AI core (bloom-lit, orbiting sentiment
// satellites). Lazy-loaded so it never blocks first paint.
const CoreScene = dynamic(() => import("@/components/3d/CoreScene"), {
  ssr: false,
  loading: () => null,
});

const FEATURES = [
  {
    icon: Sparkles,
    title: "Aspect-Based Sentiment",
    body: "Battery, camera, display — see exactly which features customers love or complain about, per aspect, not just overall.",
  },
  {
    icon: ShieldCheck,
    title: "Quality & Suspicion Signals",
    body: "Review detection, duplicate and near-duplicate flags, gibberish and spam heuristics — with transparent reasons, never silent deletes.",
  },
  {
    icon: BarChart3,
    title: "Explainable Predictions",
    body: "Every prediction ships with confidence and the model features that contributed most. No black boxes.",
  },
];

const PREVIEW = [
  { text: "Battery life is excellent and lasts all day.", sentiment: "Positive" },
  { text: "Camera quality is terrible, photos are blurry.", sentiment: "Negative" },
  { text: "The package arrived yesterday. It has a 6.5 inch display.", sentiment: "Neutral" },
  { text: "Battery is amazing but the camera is disappointing.", sentiment: "Mixed" },
] as const;

export default function LandingPage() {
  const [sample, setSample] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const loadSample = useCallback(async () => {
    setLoading(true);
    try {
      const { analyzeText } = await import("@/lib/api");
      const sampleCsv = await fetch("/sample_reviews.csv").then((r) => r.text());
      const lines = sampleCsv
        .split("\n")
        .slice(1)
        .map((l) => (l.match(/"(.*)"/) ?? [])[1] ?? "")
        .filter(Boolean);
      const result = await analyzeText(lines.join("\n\n"));
      setSample(result);
      sessionStorage.setItem("analysisId", result.analysis_id);
    } catch {
      // Landing page stays functional without the backend.
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Neural-core 3D background: covers exactly the first viewport so the
          core is centered behind the hero (not drooping down the page).
          Lazy-loaded, failure-safe, scrim keeps hero text readable. */}
      <div className="absolute inset-x-0 top-0 h-screen -z-10" aria-hidden>
        <Scene3DBoundary>
          <CoreScene />
        </Scene3DBoundary>
      </div>
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-screen -z-10"
        aria-hidden
        style={{
          background:
            "radial-gradient(ellipse 58% 42% at 50% 42%, rgba(3,7,18,0.45), transparent 70%)",
        }}
      />

      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-sky-400 to-indigo-600 shadow-glow" />
          <span className="text-sm font-semibold tracking-wide text-slate-200">
            Sentiment Engine
          </span>
        </div>
        <Link
          href="/analysis"
          className="rounded-xl border border-sky-400/20 bg-sky-400/10 px-4 py-2 text-sm text-sky-200 transition hover:bg-sky-400/20"
        >
          Open Dashboard
        </Link>
      </header>

      <main className="relative z-10 mx-auto max-w-6xl px-6">
        {/* Hero */}
        <section className="pt-16 pb-16 text-center">
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15 }}
            className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-sky-400/25 bg-sky-400/10 px-4 py-1.5 text-xs text-sky-200 backdrop-blur-md"
          >
            <Sparkles size={13} className="text-sky-300" />
            Explainable NLP · Aspect intelligence · Quality scoring
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mx-auto max-w-3xl text-4xl font-bold leading-tight tracking-tight text-white sm:text-6xl"
          >
            One core. Every opinion decoded.
            <br />
            <span className="bg-gradient-to-r from-sky-400 via-blue-300 to-violet-400 bg-clip-text text-transparent">
              E-Commerce Smart Review &amp; Sentiment Engine
            </span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
            className="mx-auto mt-6 max-w-xl text-lg text-slate-400"
          >
            Transform customer feedback into explainable product intelligence.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
          >
            <Link
              href="/analysis"
              className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 px-6 py-3 font-medium text-white shadow-glow transition hover:opacity-90"
            >
              Analyze Reviews
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
            </Link>
            <button
              onClick={loadSample}
              disabled={loading}
              className="rounded-xl border border-sky-400/20 bg-slate-900/50 px-6 py-3 font-medium text-slate-200 backdrop-blur-md transition hover:bg-slate-800/60 disabled:opacity-50"
            >
              {loading ? "Analyzing sample…" : "Try the sample dataset"}
            </button>
          </motion.div>

          {/* Core stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.45 }}
            className="mx-auto mt-9 flex max-w-lg flex-wrap items-center justify-center gap-8"
          >
            {[
              { value: "2", label: "ML models" },
              { value: "297k", label: "TF-IDF features" },
              { value: "18", label: "aspect types" },
            ].map((s) => (
              <div key={s.label} className="text-center">
                <p className="font-mono text-xl font-semibold text-sky-300">{s.value}</p>
                <p className="text-[10px] uppercase tracking-widest text-slate-500">{s.label}</p>
              </div>
            ))}
          </motion.div>

          {sample && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 text-sm text-sky-300 hover:underline"
              >
                Sample ready — {sample.statistics.reviews_analyzed} reviews analyzed. Open the dashboard
                <ArrowRight size={14} />
              </Link>
            </motion.div>
          )}
        </section>

        {/* Floating review cards preview */}
        <section className="grid gap-4 pb-20 sm:grid-cols-2 lg:grid-cols-4" aria-label="Example analyses">
          {PREVIEW.map((p, i) => (
            <motion.div
              key={p.text}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass glass-hover border-sky-400/10 p-4 backdrop-blur-xl"
            >
              <p className="text-sm text-slate-300">&ldquo;{p.text}&rdquo;</p>
              <div className="mt-3">
                <SentimentBadge sentiment={p.sentiment} />
              </div>
            </motion.div>
          ))}
        </section>

        {/* Features */}
        <section className="grid gap-6 pb-24 md:grid-cols-3">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
            >
              <div className="glass glass-hover h-full border-sky-400/10 p-6 backdrop-blur-xl">
                <div className="mb-4 inline-flex rounded-xl bg-sky-400/10 p-3 text-sky-300">
                  <f.icon size={22} />
                </div>
                <h3 className="font-medium text-slate-100">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{f.body}</p>
              </div>
            </motion.div>
          ))}
        </section>
      </main>

      <footer className="relative z-10 border-t border-white/5 py-8 text-center text-xs text-slate-600">
        E-Commerce Smart Review &amp; Sentiment Engine — Next.js · FastAPI · scikit-learn.
        Confidence reflects model certainty, not guaranteed correctness.
      </footer>
    </div>
  );
}
