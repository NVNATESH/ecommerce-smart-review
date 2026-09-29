"""Shared response schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


class HealthResponse(BaseModel):
    success: bool = True
    status: str
    app: str
    version: str
    models_loaded: bool
