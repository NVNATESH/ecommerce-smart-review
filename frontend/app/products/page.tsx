"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FolderOpen, Plus, Trash2 } from "lucide-react";

import { AppShell, PageHeader } from "@/components/layout/AppShell";
import { EmptyState, ErrorState, GlassCard, Skeleton, StatusBadge } from "@/components/ui/primitives";
import { addProductReviews, deleteProduct, listProducts } from "@/lib/api";
import type { ProductListItem } from "@/lib/api";

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductListItem[] | null>(null);
  const [error, setError] = useState<{ message: string; code?: string } | null>(null);
  const [addingTo, setAddingTo] = useState<string | null>(null);
  const [newText, setNewText] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  const load = useCallback(async () => {
    try {
      const res = await listProducts();
      setProducts(res.products);
    } catch (e) {
      setError({ message: e instanceof Error ? e.message : "Could not load products." });
      setProducts([]);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openProduct = (p: ProductListItem) => {
    // the product id doubles as the stable analysis key (survives restarts)
    sessionStorage.setItem("analysisId", p.id);
    router.push("/dashboard");
  };

  const addReviews = async (p: ProductListItem) => {
    if (!newText.trim() || busy) return;
    setBusy(true);
    try {
      const texts = newText.split("\n").map((t) => t.trim()).filter(Boolean);
      await addProductReviews(p.id, texts);
      setNewText("");
      setAddingTo(null);
      await load();
    } catch (e) {
      setError({ message: e instanceof Error ? e.message : "Could not add reviews." });
    } finally {
      setBusy(false);
    }
  };

  const remove = async (p: ProductListItem) => {
    if (!confirm(`Delete "${p.name}" and its stored reviews?`)) return;
    await deleteProduct(p.id);
    await load();
  };

  return (
    <AppShell>
      <PageHeader
        title="My Products"
        subtitle="Stored feedback reviews per product — add new reviews anytime and the analysis updates."
      />
      {error && <ErrorState message={error.message} code={error.code} />}
      {products === null && !error && <Skeleton className="h-40 w-full" />}
      {products && products.length === 0 && (
        <EmptyState
          title="No stored products yet"
          description="Analyze reviews on the Analysis page and give the analysis a product name — it will be saved here."
        />
      )}
      {products && products.length > 0 && (
        <div className="space-y-4">
          {products.map((p) => (
            <GlassCard key={p.id} className="p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-base font-medium text-slate-100">{p.name}</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    {p.review_count} reviews · updated {new Date(p.updated_at).toLocaleString()}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    {p.verdict && <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-slate-300">{p.verdict}</span>}
                    {p.trust !== null && p.trust !== undefined && (
                      <span className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-2 py-0.5 text-[11px] text-emerald-300">Trust {Number(p.trust).toFixed(0)}</span>
                    )}
                    {p.quality !== null && p.quality !== undefined && (
                      <span className="rounded-full border border-sky-400/25 bg-sky-400/10 px-2 py-0.5 text-[11px] text-sky-300">Quality {Number(p.quality).toFixed(0)}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {p.analysis_id && (
                    <button
                      onClick={() => openProduct(p)}
                      className="rounded-xl border border-sky-400/30 bg-sky-400/10 px-4 py-2 text-xs font-medium text-sky-200 transition hover:bg-sky-400/20"
                    >
                      Open dashboard
                    </button>
                  )}
                  <button
                    onClick={() => setAddingTo(addingTo === p.id ? null : p.id)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-slate-200 transition hover:bg-white/10"
                  >
                    <Plus size={13} /> Add reviews
                  </button>
                  <button
                    onClick={() => remove(p)}
                    aria-label={`Delete ${p.name}`}
                    className="rounded-xl border border-rose-400/20 bg-rose-400/5 p-2 text-rose-300 transition hover:bg-rose-400/15"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              {addingTo === p.id && (
                <div className="mt-4">
                  <textarea
                    value={newText}
                    onChange={(e) => setNewText(e.target.value)}
                    rows={4}
                    placeholder="Paste new reviews — one per line. They will be added to this product and the full analysis re-run."
                    aria-label={`New reviews for ${p.name}`}
                    className="w-full resize-y rounded-xl border border-white/10 bg-black/20 p-3 text-sm text-slate-200 placeholder:text-slate-600 focus:border-accent-blue/50 focus:outline-none"
                  />
                  <div className="mt-2 flex items-center justify-between">
                    <p className="text-xs text-slate-600">{newText.split("\n").filter((t) => t.trim()).length} new review(s)</p>
                    <button
                      onClick={() => addReviews(p)}
                      disabled={busy || !newText.trim()}
                      className="rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 px-4 py-2 text-xs font-medium text-white transition hover:opacity-90 disabled:opacity-40"
                    >
                      {busy ? "Re-analyzing…" : "Add & re-analyze"}
                    </button>
                  </div>
                </div>
              )}
            </GlassCard>
          ))}
          <GlassCard className="flex items-center gap-3 p-4">
            <FolderOpen size={18} className="text-slate-500" />
            <p className="text-xs text-slate-500">
              Products persist on disk (backend/data/products/) — they survive server restarts. Use the Compare page to compare two or more.
            </p>
          </GlassCard>
        </div>
      )}
    </AppShell>
  );
}
