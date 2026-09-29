"""POST /api/analyze/csv - asynchronous CSV analysis job.

Upload -> create analysis job -> background processing -> frontend polls
GET /api/analysis/{id}/status -> completed. No Celery/Redis needed for v1.
"""
from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, Depends, UploadFile

from api.dependencies import get_pipeline, get_store, store_lock
from api.errors import InputValidationError, ModelNotLoadedError
from schemas.analysis import AnalysisStatusResponse
from services.analysis_service import AnalysisPipeline, AnalysisStore
from services.input_service import parse_csv_upload

logger = logging.getLogger("app.routes.upload")
router = APIRouter()


def _run_job(analysis_id: str, reviews: list[str], pipeline: AnalysisPipeline, store: AnalysisStore) -> None:
    try:
        with store_lock:
            pipeline.run(
                analysis_id, reviews, source="csv", store=store,
            )
    except Exception as exc:
        logger.exception("Analysis job %s failed", analysis_id)
        with store_lock:
            store.set_failed(analysis_id, "ANALYSIS_FAILED", "The analysis could not be completed.")


@router.post("/analyze/csv", response_model=AnalysisStatusResponse)
async def analyze_csv(
    file: UploadFile,
    pipeline: AnalysisPipeline = Depends(get_pipeline),
    store: AnalysisStore = Depends(get_store),
):
    head = await file.read(8)
    await file.seek(0)  # rewind: head peek advanced the stream
    content = await file.read()
    size = len(content)

    reviews = parse_csv_upload(file.filename, size, head, content)
    analysis_id = store.create(source="csv", filename=file.filename)
    logger.info(
        "CSV analysis %s queued: %d rows from %s", analysis_id, len(reviews), "uploaded file",
    )

    thread = threading.Thread(
        target=_run_job, args=(analysis_id, reviews, pipeline, store), daemon=True,
        name=f"analysis-{analysis_id}",
    )
    thread.start()

    return AnalysisStatusResponse(
        analysis_id=analysis_id, status="processing", progress=0, stage="Queued",
    )
