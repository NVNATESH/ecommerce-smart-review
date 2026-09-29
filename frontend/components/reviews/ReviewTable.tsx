"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import type { ReviewPage, ReviewResult } from "@/lib/types";
import { getReviews } from "@/lib/api";
import {
  ConfidenceBadge,
  ErrorState,
  SentimentBadge,
  Skeleton,
  StatusBadge,
} from "@/components/ui/primitives";
import { truncate } from "@/lib/utils";

export interface ReviewFilters {
  status?: string;
  sentiment?: string;
  suspicious?: boolean;
  search?: string;
  sort?: string;
  order?: string;
}

export function ReviewTable({
  analysisId,
  filters: initialFilters = {},
  showFilters = true,
  pageSize = 25,
  onSelect,
}: {
  analysisId: string;
  filters?: ReviewFilters;
  showFilters?: boolean;
  pageSize?: number;
  onSelect?: (review: ReviewResult) => void;
}) {
  const [data, setData] = useState<ReviewPage | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ message: string; code?: string } | null>(null);
  const [filters, setFilters] = useState<ReviewFilters>(initialFilters);
  const [searchInput, setSearchInput] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getReviews(analysisId, { page, page_size: pageSize, ...filters })
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((e) => {
        if (!cancelled) setError({ message: e.message, code: e.code });
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [analysisId, page, pageSize, filters]);

  if (error) return <ErrorState message={error.message} code={error.code} />;

  return (
    <div className="space-y-3">
      {showFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (setPage(1), setFilters((f) => ({ ...f, search: searchInput })))}
              placeholder="Search reviews…"
              aria-label="Search reviews"
              className="w-56 rounded-xl border border-white/10 bg-white/5 py-2 pl-9 pr-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-accent-blue/50 focus:outline-none"
            />
          </div>
          <select
            value={filters.sentiment ?? ""}
            onChange={(e) => (setPage(1), setFilters((f) => ({ ...f, sentiment: e.target.value || undefined })))}
            aria-label="Filter by sentiment"
            className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 focus:outline-none"
          >
            <option value="">All sentiments</option>
            <option>Positive</option>
            <option>Neutral</option>
            <option>Negative</option>
            <option>Mixed</option>
          </select>
          <select
            value={filters.status ?? ""}
            onChange={(e) => (setPage(1), setFilters((f) => ({ ...f, status: e.target.value || undefined })))}
            aria-label="Filter by review status"
            className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 focus:outline-none"
          >
            <option value="">All statuses</option>
            <option>VALID</option>
            <option>UNCERTAIN</option>
            <option>INVALID</option>
          </select>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-400">
            <input
              type="checkbox"
              checked={filters.suspicious === true}
              onChange={(e) => (setPage(1), setFilters((f) => ({ ...f, suspicious: e.target.checked || undefined })))}
              className="rounded border-white/20 bg-white/5"
            />
            Suspicious only
          </label>
          <select
            value={`${filters.sort ?? "id"}-${filters.order ?? "asc"}`}
            onChange={(e) => {
              const [sort, order] = e.target.value.split("-");
              setFilters((f) => ({ ...f, sort, order }));
            }}
            aria-label="Sort reviews"
            className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300 focus:outline-none"
          >
            <option value="id-asc">Newest first</option>
            <option value="id-desc">Oldest first</option>
            <option value="confidence-desc">Confidence ↓</option>
            <option value="confidence-asc">Confidence ↑</option>
            <option value="suspicion_score-desc">Suspicion ↓</option>
            <option value="word_count-asc">Shortest first</option>
          </select>
        </div>
      )}

      {loading && !data ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : data && data.reviews.length === 0 ? (
        <p className="py-10 text-center text-sm text-slate-500">No reviews match these filters.</p>
      ) : data ? (
        <div className="overflow-hidden rounded-2xl border border-white/10">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-left text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Review</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="hidden px-4 py-3 font-medium md:table-cell">Sentiment</th>
                <th className="hidden px-4 py-3 font-medium sm:table-cell">Confidence</th>
                <th className="hidden px-4 py-3 font-medium lg:table-cell">Suspicion</th>
                <th className="hidden px-4 py-3 font-medium lg:table-cell">Aspects</th>
              </tr>
            </thead>
            <tbody>
              {data.reviews.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => onSelect?.(r)}
                  className={`border-t border-white/5 transition-colors hover:bg-white/[0.04] ${onSelect ? "cursor-pointer" : ""}`}
                >
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">{r.id}</td>
                  <td className="max-w-md px-4 py-3 text-slate-300">
                    {truncate(r.original_text, 120)}
                    {(r.duplicate || r.near_duplicate) && (
                      <span className="ml-2 rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-500">
                        {r.duplicate ? "dup" : "near-dup"}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={r.review_status} /></td>
                  <td className="hidden px-4 py-3 md:table-cell"><SentimentBadge sentiment={r.sentiment} /></td>
                  <td className="hidden px-4 py-3 sm:table-cell"><ConfidenceBadge confidence={r.confidence} /></td>
                  <td className="hidden px-4 py-3 lg:table-cell">
                    <span className={`font-mono text-xs ${r.suspicious ? "text-amber-400" : "text-slate-600"}`}>
                      {r.suspicion_score}
                    </span>
                  </td>
                  <td className="hidden max-w-[180px] truncate px-4 py-3 text-xs text-slate-500 lg:table-cell">
                    {r.aspects.map((a) => a.category).join(", ") || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>
            {data.total} reviews · page {data.page} of {data.total_pages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={data.page <= 1}
              aria-label="Previous page"
              className="rounded-lg border border-white/10 p-1.5 transition hover:bg-white/10 disabled:opacity-30"
            >
              <ChevronLeft size={14} />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
              disabled={data.page >= data.total_pages}
              aria-label="Next page"
              className="rounded-lg border border-white/10 p-1.5 transition hover:bg-white/10 disabled:opacity-30"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
