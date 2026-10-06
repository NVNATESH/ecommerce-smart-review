"""Pydantic request schemas (request-side validation)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from config import MAX_PASTED_TEXT_LENGTH


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., description="Raw pasted reviews, one per line or paragraph.")
    product_name: str | None = Field(None, max_length=80, description="Optional product name — saves the analysis as/into this product.")

    @field_validator("text")
    @classmethod
    def text_must_be_string(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("text must be a string")
        return v

    model_config = {"json_schema_extra": {"example": {"text": "Battery life is excellent.\nThe camera is terrible."}}}


class ReviewQueryParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
