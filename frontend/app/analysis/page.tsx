"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ClipboardPaste, UploadCloud } from "lucide-react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { UploadZone } from "@/components/upload/UploadZone";
import { AnalysisProgress } from "@/components/upload/AnalysisProgress";
import { ErrorState, GlassCard } from "@/components/ui/primitives";
import { analyzeText, getAnalysisStatus, uploadCSV, ApiRequestError } from "@/lib/api";
import type { AnalysisResponse } from "@/lib/types";
import { useAnalysisStore } from "@/lib/store";

type Mode = "paste" | "upload" | null;

export default function AnalysisPage() {
  const [mode, setMode] = useState<Mode>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<{ message: string; code?: string } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const setAnalysis = useAnalysisStore((s) => s.setAnalysis);
  const router = useRouter();

  const handleResult = useCallback(
    (result: AnalysisResponse | string) => {
      const id = typeof result === "string" ? result : result.analysis_id;
      sessionStorage.setItem("analysisId", id);
      setAnalysis(
        id,
        typeof result === "string" ? null : (result as AnalysisResponse),
      );
      setDone(true);
      setTimeout(() => router.push("/dashboard"), 700);
    },
    [setAnalysis, router],
  );

  const analyzePasted = useCallback(async () => {
    setBusy(true);
    setError(null);
    setMode("paste");
    setProgress(10);
    setStage("Validating...");
    try {
      const result = await analyzeText(text);
      setProgress(100);
      handleResult(result);
    } catch (e) {
      if (e instanceof ApiRequestError) setError({ message: e.message, code: e.code });
      else setError({ message: "Could not reach the analysis server. Is the backend running?" });
      setBusy(false);
    }
  }, [text, handleResult]);

  const analyzeFile = useCallback(
    async (file: File) => {
      setBusy(true);
      setError(null);
      setMode("upload");
      setDone(false);
      setStage("Uploading...");
      setProgress(2);
      try {
        const status = await uploadCSV(file, (pct) => {
          setStage("Uploading...");
          setProgress(Math.max(2, Math.round(pct * 0.1)));
        });
        const poll = async () => {
          const s = await getAnalysisStatus(status.analysis_id);
          setProgress(s.progress);
          setStage(s.stage);
          if (s.status === "completed") {
            setProgress(100);
            handleResult(s.analysis_id);
          } else if (s.status === "failed") {
            setError({ message: s.error?.message ?? "Analysis failed.", code: s.error?.code });
            setBusy(false);
          } else {
            setTimeout(poll, 600);
          }
        };
        await poll();
      } catch (e) {
        if (e instanceof ApiRequestError) {
          setError({ message: e.message, code: e.code });
          if (e.details && typeof e.details.detected_columns !== "undefined") {
            setError({
              message: `Review column not found. Detected columns: ${(e.details.detected_columns as string[]).join(", ")}`,
              code: e.code,
            });
          }
        } else {
          setError({ message: "Could not reach the analysis server. Is the backend running?" });
        }
        setBusy(false);
      }
    },
    [handleResult],
  );

  return (
    <AppShell>
      <PageHeader
        title="Analyze Reviews"
        subtitle="Paste reviews or upload a CSV — validation, review detection, sentiment, aspects and quality run automatically."
        right={
          <button
            onClick={() => {
              setMode(null);
              setError(null);
              setDone(false);
              setProgress(0);
            }}
            className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/10"
          >
            New analysis
          </button>
        }
      />

      <div className="space-y-6">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Paste */}
          <GlassCard className="p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
              <ClipboardPaste size={15} className="text-accent-cyan" /> Paste reviews
            </h2>
            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={busy}
              rows={9}
              placeholder={"One review per line (or separated by blank lines):\n\nThe battery life is excellent and the display is bright.\nCamera quality is terrible and the microphone is weak.\nThe battery is amazing but the camera is disappointing."}
              aria-label="Paste reviews"
              className="w-full resize-y rounded-xl border border-white/10 bg-black/20 p-4 text-sm leading-relaxed text-slate-200 placeholder:text-slate-600 focus:border-accent-blue/50 focus:outline-none disabled:opacity-50"
            />
            <div className="mt-3 flex items-center justify-between">
              <p className="text-xs text-slate-600">{text.trim() ? text.trim().split(/\n+/).length : 0} line(s) of input</p>
              <button
                onClick={analyzePasted}
                disabled={busy || !text.trim()}
                className="rounded-xl bg-gradient-to-r from-accent-blue to-accent-violet px-5 py-2 text-sm font-medium text-white shadow-glow transition hover:opacity-90 disabled:opacity-40 disabled:shadow-none"
              >
                {busy && mode === "paste" ? "Analyzing…" : "Analyze Text"}
              </button>
            </div>
          </GlassCard>

          {/* Upload */}
          <GlassCard className="p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
              <UploadCloud size={15} className="text-accent-violet" /> Upload CSV
            </h2>
            <UploadZone onFile={analyzeFile} disabled={busy} />
          </GlassCard>
        </div>

        {(busy || done || progress > 0) && (
          <AnalysisProgress progress={progress} stage={stage} done={done} />
        )}

        {error && <ErrorState message={error.message} code={error.code} />}
      </div>
    </AppShell>
  );
}
