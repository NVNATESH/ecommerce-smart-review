"""GET /api/export/{analysis_id} - downloadable, sanitized results."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from api.dependencies import get_model_manager, get_store
from api.errors import AnalysisNotFoundError
from ml.model_manager import ModelManager
from services.analysis_service import AnalysisStore
from services.export_service import (
    analysis_json,
    aspects_csv,
    metrics_json,
    quality_json,
    reviews_csv,
)

logger = logging.getLogger("app.routes.export")
router = APIRouter()

FORMATS = ("reviews_csv", "aspects_csv", "quality_json", "metrics_json", "analysis_json")


@router.get("/export/{analysis_id}")
def export_results(
    analysis_id: str,
    format: str = Query(..., description=f"One of: {', '.join(FORMATS)}"),
    store: AnalysisStore = Depends(get_store),
    manager: ModelManager = Depends(get_model_manager),
):
    if format not in FORMATS:
        raise AnalysisNotFoundError(
            "UNSUPPORTED_EXPORT_FORMAT",
            f"Unsupported export format '{format}'.",
            {"supported_formats": list(FORMATS)},
        )

    summary = store.get(analysis_id)
    if format == "metrics_json":
        # model metrics do not depend on an analysis run
        if not manager.loaded:
            raise AnalysisNotFoundError("MODELS_NOT_LOADED", "ML models are not loaded.")
        content, media_type, filename = metrics_json(manager.metadata)
    else:
        if summary is None or summary.get("status") != "completed":
            raise AnalysisNotFoundError("ANALYSIS_NOT_FOUND", "Analysis not found or not ready.")
        reviews = store.get_reviews(analysis_id) or []
        if format == "reviews_csv":
            content, media_type, filename = reviews_csv(reviews, analysis_id)
        elif format == "aspects_csv":
            content, media_type, filename = aspects_csv(
                _aspects_as_objects(summary), analysis_id,
            )
        elif format == "quality_json":
            content, media_type, filename = quality_json(summary)
        else:
            content, media_type, filename = analysis_json(summary, reviews)

    logger.info("Export %s: format=%s", analysis_id, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _aspects_as_objects(summary: dict):
    """Aspect summaries live in the store as dicts; export needs attribute access."""
    from schemas.analysis import AspectSummary

    return [AspectSummary(**a) for a in summary.get("aspects", [])]
