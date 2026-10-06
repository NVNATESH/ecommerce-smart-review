"""POST /api/analyze/csv - asynchronous CSV analysis job.

Upload -> create analysis job -> background processing -> frontend polls
GET /api/analysis/{id}/status -> completed. No Celery/Redis needed for v1.
With product_name: the CSV reviews are appended to that stored product and
the combined dataset is re-analysed."""
from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, Depends, Form, UploadFile

from api.dependencies import get_pipeline, get_product_store, get_store, store_lock
from api.readiness import wait_until_ready
from api.errors import InputValidationError
from schemas.analysis import AnalysisStatusResponse
from services.analysis_service import AnalysisPipeline, AnalysisStore
from services.input_service import parse_csv_upload
from services.product_store import ProductStore

logger = logging.getLogger("app.routes.upload")
router = APIRouter()


def _run_job(analysis_id: str, texts: list[str], pipeline: AnalysisPipeline,
             store: AnalysisStore, product_id: str | None,
             products: ProductStore | None) -> None:
    try:
        pipeline.run(analysis_id, texts, source="csv", store=store)
        if product_id and products is not None:
            summary = store.get(analysis_id)
            results = store.get_reviews(analysis_id)
            if summary and results is not None:
                products.save_analysis(product_id, analysis_id, summary, results)
                store.ingest(product_id, {**summary, "analysis_id": product_id}, results)
    except Exception as exc:
        logger.exception("Analysis job %s failed", analysis_id)
        with store_lock:
            store.set_failed(analysis_id, "ANALYSIS_FAILED", "The analysis could not be completed.")


@router.post("/analyze/csv", response_model=AnalysisStatusResponse)
async def analyze_csv(
    file: UploadFile,
    product_name: str | None = Form(None, max_length=80),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
    store: AnalysisStore = Depends(get_store),
    products: ProductStore = Depends(get_product_store),
):
    head = await file.read(8)
    await file.seek(0)  # rewind: head peek advanced the stream
    content = await file.read()
    size = len(content)

    wait_until_ready()  # first CSV job waits for background NLP warm-up
    reviews = parse_csv_upload(file.filename, size, head, content)
    combined = reviews
    product_id = None
    if product_name and product_name.strip():
        product_id = products.find_or_create(product_name.strip())
        combined = products.append_reviews(product_id, reviews)

    analysis_id = store.create(source="csv", filename=file.filename)
    logger.info(
        "CSV analysis %s queued: %d rows from %s (product=%s)",
        analysis_id, len(reviews), "uploaded file", product_name,
    )

    thread = threading.Thread(
        target=_run_job,
        args=(analysis_id, combined, pipeline, store, product_id, products),
        daemon=True,
        name=f"analysis-{analysis_id}",
    )
    thread.start()

    return AnalysisStatusResponse(
        analysis_id=analysis_id, status="processing", progress=0, stage="Queued",
    )
