"use client";

import { useEffect } from "react";

import { useAnalysisStore } from "@/lib/store";

/** Ensures a summary is loaded for the active (or stored) analysis id. */
export function useAnalysis() {
  const store = useAnalysisStore();

  useEffect(() => {
    const id = store.analysisId ?? sessionStorage.getItem("analysisId");
    if (id && (!store.summary || store.summary.analysis_id !== id) && !store.loading && !store.error) {
      store.loadSummary(id);
    }
  }, [store.analysisId, store.summary, store.loading, store.error, store.loadSummary]);

  return store;
}
