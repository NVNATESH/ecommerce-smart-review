"""Product routes: store feedback reviews per product, add new reviews to an
existing product, and compare products side by side."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from api.dependencies import get_pipeline, get_product_store, get_store
from api.errors import AnalysisNotFoundError, InputValidationError, ProductNotFoundError
from api.readiness import wait_until_ready
from services.analysis_service import AnalysisPipeline, AnalysisStore
from services.product_store import ProductStore

def _aspect_rating(pos_pct: float, neg_pct: float) -> str:
    """Qualitative rating for one aspect inside one product, from the sentiment
    mix of its mentions: Best / Excellent / Good / Average / Poor / Worst."""
    score = pos_pct - neg_pct
    if score >= 60:
        return "Best"
    if score >= 20:
        return "Excellent"
    if score > 0:
        return "Good"
    if score == 0:
        return "Average"
    if score > -60:
        return "Poor"
    return "Worst"


router = APIRouter()


class AddReviewsRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1)


@router.get("/products")
def list_products(ps: ProductStore = Depends(get_product_store)):
    return {"success": True, "products": ps.list()}


@router.get("/products/{pid}")
def get_product(pid: str, ps: ProductStore = Depends(get_product_store)):
    d = ps.get(pid)
    if d is None:
        raise ProductNotFoundError()
    return {
        "success": True,
        "id": d["id"],
        "name": d["name"],
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
        "review_count": len(d["reviews"]),
        "analysis_id": d.get("analysis_id"),
        "summary": d.get("summary"),
    }


@router.post("/products/{pid}/reviews")
def add_reviews(
    pid: str,
    body: AddReviewsRequest,
    ps: ProductStore = Depends(get_product_store),
    store: AnalysisStore = Depends(get_store),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
):
    if ps.get(pid) is None:
        raise ProductNotFoundError()
    texts = [t.strip() for t in body.texts if t and t.strip()]
    if not texts:
        raise InputValidationError("EMPTY_REVIEWS", "No review text provided.")
    wait_until_ready()  # re-analysis waits for background NLP warm-up
    combined = ps.append_reviews(pid, texts)

    fresh_id = store.create(source="product")
    try:
        pipeline.run(fresh_id, combined, source="product", store=store)
    except ValueError as exc:
        store.set_failed(fresh_id, "INVALID_INPUT", str(exc))
        raise InputValidationError("INVALID_INPUT", str(exc)) from exc
    summary = store.get(fresh_id)
    results = store.get_reviews(fresh_id)
    ps.save_analysis(pid, fresh_id, summary, results)
    store.ingest(pid, {**summary, "analysis_id": pid}, results)
    return {
        "success": True,
        "analysis_id": fresh_id,
        "product_analysis_id": pid,
        "review_count": len(combined),
        "summary": summary,
    }


@router.get("/products/{pid}/reviews")
def product_reviews(
    pid: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sentiment: str | None = Query(None),
    search: str | None = Query(None, max_length=200),
    ps: ProductStore = Depends(get_product_store),
    store: AnalysisStore = Depends(get_store),
):
    """Paginated review records for a stored product (from its saved analysis)."""
    d = ps.get(pid)
    if d is None:
        raise ProductNotFoundError()
    from schemas.review import ReviewResult, ReviewPage

    try:
        models = [ReviewResult.model_validate(r) for r in d.get("results", [])]
    except Exception:
        models = []
    if sentiment:
        models = [m for m in models if m.sentiment.value == sentiment.capitalize()]
    if search:
        needle = search.lower()
        models = [m for m in models if needle in m.original_text.lower()]
    total = len(models)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    start = (page - 1) * page_size
    return ReviewPage(
        analysis_id=pid, page=page, page_size=page_size, total=total,
        total_pages=total_pages, reviews=models[start:start + page_size],
    )


@router.delete("/products/{pid}")
def delete_product(
    pid: str,
    ps: ProductStore = Depends(get_product_store),
    store: AnalysisStore = Depends(get_store),
):
    if not ps.delete(pid):
        raise ProductNotFoundError()
    store.remove(pid)
    return {"success": True}


@router.get("/compare")
def compare(ids: str = Query(..., description="Comma-separated product ids (2-4)"), ps: ProductStore = Depends(get_product_store)):
    pids = [x.strip() for x in ids.split(",") if x.strip()][:4]
    if len(pids) < 2:
        raise InputValidationError("NEED_TWO_PRODUCTS", "Provide at least two product ids to compare.")
    products = []
    aspect_rows: dict[str, dict] = {}
    for pid in pids:
        d = ps.get(pid)
        if d is None or not d.get("summary"):
            continue
        s = d["summary"]
        entry = {
            "id": pid,
            "name": d["name"],
            "verdict": (s.get("verdict") or {}).get("overall_sentiment"),
            "trust": (s.get("trust") or {}).get("score"),
            "quality": (s.get("quality") or {}).get("quality_score"),
            "positive_pct": (s.get("sentiment") or {}).get("positive_percentage"),
            "negative_pct": (s.get("sentiment") or {}).get("negative_percentage"),
            "review_count": (s.get("statistics") or {}).get("reviews_analyzed"),
        }
        products.append(entry)
        for a in s.get("aspects", []):
            score = a["positive_percentage"] - a["negative_percentage"]
            row = aspect_rows.setdefault(a["aspect"], {"aspect": a["aspect"]})
            row[d["name"]] = {"rating": _aspect_rating(a["positive_percentage"], a["negative_percentage"]), "score": round(score, 1)}
    aspect_list = [
        {"aspect": name, **{k: v for k, v in row.items() if k != "aspect"}}
        for name, row in sorted(aspect_rows.items())
    ]
    return {"success": True, "products": products, "aspects": aspect_list}
