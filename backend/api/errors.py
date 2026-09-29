"""Application error type + FastAPI exception handlers.

Raw Python exceptions never reach the frontend: every error response is a
structured JSON body with a stable machine-readable code and a safe message.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")


class AppError(Exception):
    """Base class for expected, user-facing errors."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, code: str, message: str, details: dict | None = None,
                 status_code: int | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class InputValidationError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


class InvalidCSVError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


class AnalysisNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND


class ModelNotLoadedError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class FileSecurityError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST


def _error_payload(code: str, message: str, details: dict | None = None) -> dict:
    body: dict = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"success": False, "error": body}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload(
                "VALIDATION_ERROR",
                "The request payload failed validation.",
                {"errors": exc.errors()[:10]},
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        # Log the full traceback server-side; return a generic, safe message.
        logger.exception("Unhandled server error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(
                "INTERNAL_ERROR",
                "An unexpected error occurred while processing the request.",
            ),
        )
