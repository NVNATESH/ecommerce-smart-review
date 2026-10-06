/** Zustand store: the active analysis shared across dashboard pages. */
"use client";

import { create } from "zustand";

import type { AnalysisSummary } from "./types";

interface AnalysisState {
  analysisId: string | null;
  productName: string | null;
  summary: AnalysisSummary | null;
  loading: boolean;
  error: string | null;
  notFound: boolean;
  setAnalysis: (id: string, summary: AnalysisSummary | null, productName?: string | null) => void;
  loadSummary: (id: string) => Promise<void>;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  analysisId: null,
  productName: null,
  summary: null,
  loading: false,
  error: null,
  notFound: false,
  setAnalysis: (analysisId, summary, productName = null) =>
    set({ analysisId, summary, productName, error: null, notFound: false }),
  loadSummary: async (id) => {
    set({ loading: true, error: null, notFound: false });
    try {
      const { getAnalysis } = await import("./api");
      const summary = await getAnalysis(id);
      set({ analysisId: id, summary, loading: false });
    } catch (e) {
      const err = e as Error & { status?: number; code?: string };
      // stale analysis id (server restarted / product deleted) -> clean slate
      if (err.status === 404 || err.code === "ANALYSIS_NOT_FOUND") {
        sessionStorage.removeItem("analysisId");
        set({ analysisId: null, summary: null, loading: false, notFound: true, error: null });
      } else {
        set({
          loading: false,
          error: e instanceof Error ? e.message : "Failed to load analysis.",
        });
      }
    }
  },
  reset: () =>
    set({ analysisId: null, productName: null, summary: null, error: null, notFound: false }),
}));
