/** Zustand store: the active analysis shared across dashboard pages. */
"use client";

import { create } from "zustand";

import type { AnalysisSummary } from "./types";

interface AnalysisState {
  analysisId: string | null;
  summary: AnalysisSummary | null;
  loading: boolean;
  error: string | null;
  setAnalysis: (id: string, summary: AnalysisSummary | null) => void;
  loadSummary: (id: string) => Promise<void>;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  analysisId: null,
  summary: null,
  loading: false,
  error: null,
  setAnalysis: (analysisId, summary) => set({ analysisId, summary, error: null }),
  loadSummary: async (id) => {
    set({ loading: true, error: null });
    try {
      const { getAnalysis } = await import("./api");
      const summary = await getAnalysis(id);
      set({ analysisId: id, summary, loading: false });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "Failed to load analysis.",
      });
    }
  },
  reset: () => set({ analysisId: null, summary: null, error: null }),
}));
