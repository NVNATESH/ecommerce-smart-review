"use client";

import { useCallback, useEffect, useState } from "react";
import { Scale } from "lucide-react";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { EmptyState, ErrorState, GlassCard, Skeleton } from "@/components/ui/primitives";
import { compareProducts, listProducts } from "@/lib/api";
import type { CompareResponse, ProductListItem } from "@/lib/api";
import type { CompareProduct } from "@/lib/api";

const SERIES_COLORS = ["#22D3EE", "#F5A623", "#A78BFA", "#34D399"];

export default function ComparePage() {
  const [products, setProducts] = useState<ProductListItem[] | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [error, setError] = useState<{ message: string; code?: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<null | {
    products: {
      id: string; name: string; verdict?: string | null; trust?: number | null;
      quality?: number | null; positive_pct?: number | null;
      negative_pct?: number | null; review_count?: number | null;
    }[];
    aspects: CompareResponse["aspects"];
  } | null>(null);

  const loadList = useCallback(async () => {
    try {
      const res = await listProducts();
      setProducts(res.products);
      if (res.products.length >= 2) setSelected(res.products.slice(0, 2).map((p) => p.id));
    } catch (e) {
      setError({ message: e instanceof Error ? e.message : "Could not load products." });
      setProducts([]);
    }
  }, []);

  useEffect(() => {
    loadList();
  }, [loadList]);

  const runCompare = useCallback(async () => {
    if (selected.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      setData(await compareProducts(selected));
    } catch (e) {
      setError({ message: e instanceof Error ? e.message : "Compare failed." });
    } finally {
      setLoading(false);
    }
  }, [selected]);

  const toggle = (id: string) => {
    setSelected((sel) =>
      sel.includes(id) ? sel.filter((x) => x !== id) : sel.length >= 4 ? sel : [...sel, id],
    );
  };

  const radarRows = (data?.aspects ?? []).map((a) => ({
    aspect: a.aspect,
    ...Object.fromEntries(data!.products.map((p) => [p.name, Number(a.scores?.[p.name] ?? 0)])),
  }));

  return (
    <AppShell>
      <PageHeader
        title="Compare Products"
        subtitle="Side-by-side verdicts, trust, quality and aspect scores for stored products."
      />

      {error && <ErrorState message={error.message} code={error.code} />}
      {products === null && !error && <Skeleton className="h-40 w-full" />}

      {products && products.length < 2 && !error && (
        <EmptyState
          title="Need at least two stored products"
          description="Analyze reviews for two different products (give each analysis a product name), then compare them here."
        />
      )}

      {products && products.length >= 2 && (
        <div className="space-y-6">
          <GlassCard className="p-5">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-200">
              <Scale size={15} className="text-accent-cyan" /> Select products (2–4)
            </h3>
            <div className="flex flex-wrap gap-2">
              {products.map((p) => {
                const on = selected.includes(p.id);
                return (
                  <button
                    key={p.id}
                    onClick={() => toggle(p.id)}
                    aria-pressed={on}
                    className={`rounded-xl border px-3.5 py-2 text-xs font-medium transition ${
                      on
                        ? "border-accent-cyan/60 bg-accent-cyan/15 text-accent-cyan"
                        : "border-white/10 bg-white/5 text-slate-400 hover:bg-white/10"
                    }`}
                  >
                    {p.name} · {p.review_count} reviews
                  </button>
                );
              })}
            </div>
            <button
              onClick={runCompare}
              disabled={selected.length < 2 || loading}
              className="mt-4 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-glow transition hover:opacity-90 disabled:opacity-40"
            >
              {loading ? "Comparing…" : "Compare selected"}
            </button>
          </GlassCard>

          {loading && <Skeleton className="h-64 w-full" />}

          {data && data.products.length >= 2 && (
            <>
              {/* summary cards per product */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {data.products.map((p) => (
                  <GlassCard key={p.id} className="p-4">
                    <p className="truncate text-sm font-medium text-slate-100">{p.name}</p>
                    <p className="mt-1 text-[11px] uppercase tracking-wider text-slate-500">{p.verdict}</p>
                    <div className="mt-2 space-y-1 text-xs">
                      <div className="flex justify-between"><span className="text-slate-500">Trust</span><span className="font-mono text-emerald-300">{p.trust?.toFixed(0) ?? "—"}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Quality</span><span className="font-mono text-sky-300">{p.quality?.toFixed(0) ?? "—"}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Positive</span><span className="font-mono text-emerald-300">{p.positive_pct?.toFixed(0) ?? "—"}%</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Negative</span><span className="font-mono text-rose-300">{p.negative_pct?.toFixed(0) ?? "—"}%</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Reviews</span><span className="font-mono text-slate-300">{p.review_count ?? "—"}</span></div>
                    </div>
                  </GlassCard>
                ))}
              </div>

              {/* aspect radar overlay */}
              {data.aspects.length >= 3 && (
                <GlassCard className="p-5">
                  <h3 className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-200">
                    <Scale size={15} className="text-accent-cyan" /> Aspect sentiment score overlay
                  </h3>
                  <p className="mb-2 text-[11px] text-slate-600">
                    Score = positive% − negative% per aspect. Higher is better.
                  </p>
                  <ResponsiveContainer width="100%" height={340}>
                    <RadarChart data={radarRows} outerRadius="70%">
                      <PolarGrid stroke="rgba(255,255,255,0.08)" />
                      <PolarAngleAxis dataKey="aspect" tick={{ fill: "#94A3B8", fontSize: 11 }} />
                      <PolarRadiusAxis domain={[-100, 100]} tick={{ fill: "#475569", fontSize: 10 }} />
                      {data.products.map((p, i) => (
                        <Radar
                          key={p.id}
                          name={p.name}
                          dataKey={p.name}
                          stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                          fill={SERIES_COLORS[i % SERIES_COLORS.length]}
                          fillOpacity={0.18}
                        />
                      ))}
                      <Legend wrapperStyle={{ fontSize: 12, color: "#94A3B8" }} />
                      <Tooltip contentStyle={{ background: "rgba(11,16,32,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, color: "#E2E8F0", fontSize: 12 }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </GlassCard>
              )}

              {/* per-aspect table */}
              <GlassCard className="overflow-x-auto p-0">
                <table className="w-full text-sm">
                  <thead className="bg-white/5 text-left text-xs uppercase tracking-wider text-slate-500">
                    <tr>
                      <th className="px-4 py-3 font-medium">Aspect</th>
                      {data.products.map((p) => (
                        <th key={p.id} className="px-4 py-3 font-medium">{p.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.aspects.map((row) => {
                      const cell = (p: CompareProduct) => {
                        const v = row.ratings?.[p.name];
                        const s = row.scores?.[p.name];
                        const color =
                          v === "Best" || v === "Excellent"
                            ? "text-emerald-300"
                            : v === "Good"
                              ? "text-sky-300"
                              : v === "Poor" || v === "Worst"
                                ? "text-rose-300"
                                : "text-slate-400";
                        return (
                          <td key={p.id} className="px-4 py-2.5">
                            {v ? (
                              <span className={`font-medium ${color}`}>
                                {v}
                                <span className="ml-1.5 font-mono text-[10px] text-slate-600">
                                  ({s > 0 ? "+" : ""}{Number(s).toFixed(0)})
                                </span>
                              </span>
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                        );
                      };
                      return (
                        <tr key={row.aspect} className="border-t border-white/5">
                          <td className="px-4 py-2.5 font-medium text-slate-300">{row.aspect}</td>
                          {data.products.map((p) => cell(p))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </GlassCard>
            </>
          )}
        </div>
      )}
    </AppShell>
  );
}
