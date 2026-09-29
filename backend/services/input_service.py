"""Input parsing: pasted text splitting and CSV column detection/parsing.

Routes stay thin; all parsing + validation lives here.
"""
from __future__ import annotations

import io
import logging

import pandas as pd

from api.errors import AppError, InvalidCSVError, InputValidationError
from config import MAX_REVIEW_LENGTH, MAX_ROWS, MAX_TOTAL_TEXT_LENGTH, REVIEW_COLUMNS
from security.file_security import validate_upload
from validation.input_validator import validate_text_input

logger = logging.getLogger("app.input")


def parse_pasted_text(text: str) -> list[str]:
    """Split pasted input into individual reviews (blank-line or line separated)."""
    result = validate_text_input(text)
    if not result.valid:
        raise InputValidationError(result.code, result.message)

    # Prefer paragraph breaks; fall back to single newlines, then numbered lines.
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    if len(chunks) <= 1:
        chunks = [c.strip() for c in text.splitlines() if c.strip()]
    if len(chunks) <= 1:
        chunks = [c.strip() for c in text.split("\r") if c.strip()]

    # Drop obvious list numbering prefixes ("1.", "1)", "Review 1:")
    cleaned: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) > MAX_REVIEW_LENGTH:
            chunk = chunk[:MAX_REVIEW_LENGTH]
        cleaned.append(chunk)

    cleaned = [c for c in cleaned if c]
    if not cleaned:
        raise InputValidationError("NO_VALID_REVIEWS", "No valid reviews were found in the input.")
    return cleaned


def detect_review_column(columns: list[str]) -> str | None:
    lowered = {c.lower().strip(): c for c in columns}
    for candidate in REVIEW_COLUMNS:
        if candidate in lowered:
            return lowered[candidate]
    # partial match fallback
    for candidate in REVIEW_COLUMNS:
        for low, original in lowered.items():
            if candidate in low:
                return original
    return None


def parse_csv_upload(filename: str | None, size: int, head: bytes, content: bytes) -> list[str]:
    """Validate + parse an uploaded CSV into a list of review strings."""
    validate_upload(filename, size, head)

    try:
        reader = pd.read_csv(io.BytesIO(content), chunksize=2048, on_bad_lines="skip")
        reviews: list[str] = []
        detected_column: str | None = None
        total_chars = 0
        for chunk in reader:
            if detected_column is None:
                detected_column = detect_review_column(list(chunk.columns))
                if detected_column is None:
                    raise InvalidCSVError(
                        "REVIEW_COLUMN_NOT_FOUND",
                        "Review column not found.",
                        {"detected_columns": [str(c) for c in chunk.columns]},
                    )
            series = chunk[detected_column].dropna().astype(str).str.strip()
            values = [v for v in series if v and v.lower() != "nan"]
            total_chars += sum(len(v) for v in values)
            reviews.extend(values)
            if len(reviews) > MAX_ROWS:
                raise AppError(
                    "TOO_MANY_ROWS",
                    f"The file exceeds the maximum of {MAX_ROWS:,} rows.",
                    status_code=413,
                )
            if total_chars > MAX_TOTAL_TEXT_LENGTH:
                raise AppError(
                    "TOTAL_TEXT_TOO_LARGE",
                    "The total text volume exceeds the processing limit.",
                    status_code=413,
                )
    except InvalidCSVError:
        raise
    except AppError:
        raise
    except Exception as exc:
        logger.warning("CSV parse failure: %s", exc)
        raise InvalidCSVError(
            "INVALID_CSV",
            "The uploaded CSV could not be processed. Please check the file encoding and format.",
        ) from exc

    if not reviews:
        raise InvalidCSVError(
            "NO_VALID_ROWS",
            "No usable reviews were found in the CSV.",
            {"detected_column": detected_column},
        )
    return reviews
