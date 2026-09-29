"""GET /api/reviews/{analysis_id} - paginated, filterable review records."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_store
from api.errors import AnalysisNotFoundError
from schemas.review import ReviewPage
from services.analysis_service import AnalysisStore

router = APIRouter()


@router.get("/reviews/{analysis_id}", response_model=ReviewPage)
def get_reviews(
    analysis_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = Query(None, description="VALID | UNCERTAIN | INVALID"),
    sentiment: str | None = Query(None, description="Positive | Negative | Neutral | Mixed"),
    suspicious: bool | None = Query(None),
    search: str | None = Query(None, max_length=200),
    sort: str = Query("id", pattern="^(id|confidence|suspicion_score|word_count)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    store: AnalysisStore = Depends(get_store),
):
    reviews = store.get_reviews(analysis_id)
    if reviews is None:
        raise AnalysisNotFoundError("ANALYSIS_NOT_FOUND", "Analysis not found or not ready.")

    filtered = reviews
    if status:
        filtered = [r for r in filtered if r.review_status.value == status.upper()]
    if sentiment:
        filtered = [r for r in filtered if r.sentiment.value == sentiment.capitalize()]
    if suspicious is not None:
        filtered = [r for r in filtered if r.suspicious == suspicious]
    if search:
        needle = search.lower()
        filtered = [r for r in filtered if needle in r.original_text.lower()]

    reverse = order == "desc"
    key = {
        "id": lambda r: r.id,
        "confidence": lambda r: r.confidence,
        "suspicion_score": lambda r: r.suspicion_score,
        "word_count": lambda r: r.word_count,
    }[sort]
    filtered = sorted(filtered, key=key, reverse=reverse)

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)
    start = (page - 1) * page_size
    chunk = filtered[start:start + page_size]

    return ReviewPage(
        analysis_id=analysis_id,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        reviews=chunk,
    )
