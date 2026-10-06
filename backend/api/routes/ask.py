"""GET /api/ask/{analysis_id}?q=... — Ask-the-Reviews question answering.

Routes stay thin: aspect routing, TF-IDF retrieval and answer synthesis live
in services/ask_service.py. The retrieval index is built lazily on the first
question and cached per analysis, so follow-up questions answer in ms."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_ask_service, get_store
from api.errors import AnalysisNotFoundError, InputValidationError
from api.readiness import wait_until_ready
from services.analysis_service import AnalysisStore
from services.ask_service import AskService

router = APIRouter()


@router.get("/ask/{analysis_id}")
def ask(
    analysis_id: str,
    q: str = Query(..., min_length=2, max_length=300, description="Your question about the analysed reviews"),
    ask_service: AskService = Depends(get_ask_service),
    store: AnalysisStore = Depends(get_store),
):
    reviews = store.get_reviews(analysis_id)
    record = store.get(analysis_id)
    if record is None or record.get("status") != "completed" or reviews is None:
        raise AnalysisNotFoundError("ANALYSIS_NOT_FOUND", "Analysis not found or not ready.")
    wait_until_ready()  # question preprocessing needs the warmed NLTK resources
    question = q.strip()
    if not question:
        raise InputValidationError("EMPTY_QUESTION", "Type a question about the reviews.")
    result = ask_service.ask(analysis_id, question, reviews, record)
    result["analysis_id"] = analysis_id
    return result
