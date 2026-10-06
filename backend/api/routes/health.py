"""GET /api/health"""
from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import get_model_manager
from api.readiness import is_ready
from config import APP_NAME, APP_VERSION
from schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    manager = get_model_manager()
    return HealthResponse(
        status="ok" if (manager.loaded and is_ready()) else ("warming" if manager.loaded else "degraded"),
        app=APP_NAME,
        version=APP_VERSION,
        models_loaded=manager.loaded,
    )
