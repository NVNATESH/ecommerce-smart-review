/** Small helpers shared across the UI. */
import type { SentimentLabel } from "./types";

export function pct(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`;
}

export function scoreColor(score: number): string {
  if (score >= 80) return "text-accent-emerald";
  if (score >= 60) return "text-accent-amber";
  return "text-accent-rose";
}

export const SENTIMENT_COLORS: Record<SentimentLabel, string> = {
  Positive: "#34D399",
  Neutral: "#94A3B8",
  Negative: "#FB7185",
  Mixed: "#FBBF24",
};

export function truncate(text: string, max = 140): string {
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

export function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export const SENTIMENTS: SentimentLabel[] = ["Positive", "Neutral", "Negative", "Mixed"];
