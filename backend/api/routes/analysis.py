"""Analysis routes: POST /api/analyze/text, GET /api/analysis/{id} (summary),
GET /api/analysis/{id}/status, GET /api/aspects/{id}, GET /api/quality/{id}."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from api.dependencies import get_pipeline, get_store
from api.errors import AnalysisNotFoundError, InputValidationError, ModelNotLoadedError
from ml.model_manager import ModelManager
from schemas.analysis import AnalysisResponse, AnalysisStatusResponse, AnalysisSummary
from schemas.review import ReviewResult
from services.analysis_service import AnalysisPipeline, AnalysisStore
from services.input_service import parse_pasted_text
from validation.schema_validator import AnalyzeTextRequest

logger = logging.getLogger("app.routes.analysis")
router = APIRouter()


@router.post("/analyze/text", response_model=AnalysisResponse)
def analyze_text(
    request: AnalyzeTextRequest,
    pipeline: AnalysisPipeline = Depends(get_pipeline),
    store: AnalysisStore = Depends(get_store),
):
    """Synchronous analysis of pasted reviews (small inputs)."""
    reviews = parse_pasted_text(request.text)
    analysis_id = store.create(source="text")
    logger.info("Text analysis %s started with %d segments", analysis_id, len(reviews))
    try:
        result = pipeline.run(analysis_id, reviews, source="text", store=store)
    except InputValidationError:
        store.set_failed(analysis_id, "INVALID_INPUT", "Input validation failed.")
        raise
    except ValueError as exc:
        store.set_failed(analysis_id, "INVALID_INPUT", str(exc))
        raise InputValidationError("INVALID_INPUT", str(exc)) from exc
    return AnalysisResponse(**{**result, "reviews": result["reviews"]})


@router.get("/analysis/{analysis_id}", response_model=AnalysisSummary)
def get_analysis(analysis_id: str, store: AnalysisStore = Depends(get_store)):
    """Summary only - detailed review records load separately (spec section 61)."""
    record = store.get(analysis_id)
    if record is None:
        raise AnalysisNotFoundError("ANALYSIS_NOT_FOUND", "Analysis not found.")
    if record.get("status") != "completed":
        raise AnalysisNotFoundError(
            "ANALYSIS_NOT_READY",
            f"Analysis is not ready (status: {record.get('status')}).",
        )
    return AnalysisSummary(**record)


@router.get("/analysis/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(analysis_id: str, store: AnalysisStore = Depends(get_store)):
    record = store.get(analysis_id)
    if record is None:
        raise AnalysisNotFoundError("ANALYSIS_NOT_FOUND", "Analysis not found.")
    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status=record.get("status", "processing"),
        progress=record.get("progress", 0),
        stage=record.get("stage", ""),
        error=record.get("error"),
    )


@router.get("/aspects/{analysis_id}")
def get_aspects(analysis_id: str, store: AnalysisStore = Depends(get_store)):
    record = store.get(analysis_id)
    if record is None or record.get("status") != "completed":
        raise AnalysisNotFoundError("ANALYSIS_NOT_FOUND", "Analysis not found or not ready.")
    return {
        "success": True,
        "analysis_id": analysis_id,
        "aspects": record.get("aspects", []),
        "most_discussed": record.get("most_discussed", []),
        "pros": record.get("pros", []),
        "cons": record.get("cons", []),
    }


@router.get("/quality/{analysis_id}")
def get_quality(analysis_id: str, store: AnalysisStore = Depends(get_store)):
    record = store.get(analysis_id)
    if record is None or record.get("status") != "completed":
        raise AnalysisNotFoundError("ANALYSIS_NOT_FOUND", "Analysis not found or not ready.")
    return {
        "success": True,
        "analysis_id": analysis_id,
        "quality": record.get("quality", {}),
        "verdict": record.get("verdict", {}),
        "statistics": record.get("statistics", {}),
    }
