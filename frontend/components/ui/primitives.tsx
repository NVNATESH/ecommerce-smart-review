"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

export function GlassCard({
  children,
  className = "",
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div className={`glass ${hover ? "glass-hover" : ""} ${className}`}>{children}</div>
  );
}

export function MetricCard({
  label,
  value,
  sub,
  icon,
  accent = "text-accent-cyan",
  delay = 0,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon?: ReactNode;
  accent?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <GlassCard hover className="p-5 relative overflow-hidden">
        <div className="absolute -right-6 -top-6 w-24 h-24 rounded-full bg-accent-blue/10 blur-2xl" />
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
            <p className={`mt-2 text-3xl font-semibold ${accent}`}>{value}</p>
            {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
          </div>
          {icon && <div className={`p-2 rounded-xl bg-white/5 ${accent}`}>{icon}</div>}
        </div>
      </GlassCard>
    </motion.div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    VALID: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    UNCERTAIN: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    INVALID: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    ACCEPT: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    "ACCEPT WITH WARNING": "bg-amber-500/15 text-amber-400 border-amber-500/30",
    REJECT: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    HIGH: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    MEDIUM: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    LOW: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium tracking-wide ${
        styles[status] ?? "bg-white/5 text-slate-300 border-white/10"
      }`}
    >
      {status}
    </span>
  );
}

export function SentimentBadge({ sentiment }: { sentiment: string }) {
  const styles: Record<string, string> = {
    Positive: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    Negative: "bg-rose-500/15 text-rose-400 border-rose-500/30",
    Neutral: "bg-slate-500/15 text-slate-300 border-slate-500/30",
    Mixed: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${
        styles[sentiment] ?? "bg-white/5 text-slate-300 border-white/10"
      }`}
    >
      {sentiment}
    </span>
  );
}

export function ConfidenceBadge({ confidence }: { confidence: number }) {
  const level = confidence >= 0.85 ? "high" : confidence >= 0.6 ? "mid" : "low";
  const color =
    level === "high"
      ? "text-emerald-400"
      : level === "mid"
        ? "text-amber-400"
        : "text-slate-400";
  return (
    <span className={`font-mono text-xs ${color}`} title="Model certainty for the predicted class — not a guarantee of correctness">
      {(confidence * 100).toFixed(0)}%
    </span>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-white/5 ${className}`}
      style={{
        backgroundImage:
          "linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 100%)",
        backgroundSize: "1000px 100%",
        animation: "shimmer 2.5s linear infinite",
      }}
    />
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <GlassCard className="p-12 text-center">
      <div className="mx-auto mb-4 h-14 w-14 rounded-2xl bg-accent-blue/10 flex items-center justify-center text-accent-blue">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M3 12h4l3-8 4 16 3-8h4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-slate-200">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </GlassCard>
  );
}

export function ErrorState({ message, code }: { message: string; code?: string }) {
  return (
    <GlassCard className="p-8 border-rose-500/20">
      <div className="flex items-start gap-4">
        <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
          </svg>
        </div>
        <div>
          <h3 className="font-medium text-rose-300">Something went wrong</h3>
          <p className="mt-1 text-sm text-slate-400">{message}</p>
          {code && <p className="mt-2 font-mono text-xs text-slate-600">Error code: {code}</p>}
        </div>
      </div>
    </GlassCard>
  );
}
