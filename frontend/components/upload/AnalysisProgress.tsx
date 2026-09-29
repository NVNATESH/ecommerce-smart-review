"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Loader2 } from "lucide-react";

export const PROGRESS_STAGES = [
  "Uploading...",
  "Validating...",
  "Detecting reviews...",
  "Removing duplicates...",
  "Preprocessing...",
  "Running sentiment model...",
  "Extracting aspects...",
  "Calculating quality...",
  "Generating dashboard...",
];

export function AnalysisProgress({
  progress,
  stage,
  done = false,
}: {
  progress: number;
  stage: string;
  done?: boolean;
}) {
  const activeIndex = PROGRESS_STAGES.findIndex((s) =>
    stage.toLowerCase().startsWith(s.slice(0, 8).toLowerCase()),
  );
  return (
    <div className="glass p-6">
      <div className="mb-3 flex items-center justify-between">
        <p className="flex items-center gap-2 text-sm text-slate-200">
          {done ? (
            <CheckCircle2 size={16} className="text-emerald-400" />
          ) : (
            <Loader2 size={16} className="animate-spin text-accent-cyan" />
          )}
          {done ? "Analysis complete" : stage}
        </p>
        <span className="font-mono text-sm text-accent-cyan">{progress}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/5">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-accent-blue via-accent-cyan to-accent-violet"
          animate={{ width: `${progress}%` }}
          transition={{ ease: "easeOut", duration: 0.4 }}
        />
      </div>
      <ul className="mt-4 grid gap-1.5 text-xs sm:grid-cols-3">
        {PROGRESS_STAGES.map((s, i) => {
          const state = done || i < activeIndex ? "done" : i === activeIndex ? "active" : "todo";
          return (
            <li
              key={s}
              className={`flex items-center gap-1.5 ${
                state === "done" ? "text-emerald-400/80" : state === "active" ? "text-accent-cyan" : "text-slate-600"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  state === "done" ? "bg-emerald-400" : state === "active" ? "bg-accent-cyan animate-pulse" : "bg-slate-700"
                }`}
              />
              {s}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
