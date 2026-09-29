"""Input validation for pasted text and CSV sources.

Every failure maps to a stable error code consumed by the frontend, e.g.:
    ""            -> EMPTY_INPUT
    "😀😀😀😀"     -> EMOJI_ONLY
    "123456789"   -> NUMBER_ONLY
    "$$$$$$$$"    -> SYMBOL_ONLY
    "https://..." -> URL_ONLY
"""
from __future__ import annotations

from dataclasses import dataclass, field

from config import MAX_PASTED_TEXT_LENGTH, MAX_REVIEW_LENGTH
from nlp.text_utils import ALPHA_RE, DIGIT_RE, EMOJI_RE, SYMBOL_RE, URL_RE


@dataclass
class ValidationResult:
    valid: bool
    code: str | None = None
    message: str | None = None
    details: dict = field(default_factory=dict)


def _strip_emoji(text: str) -> str:
    return EMOJI_RE.sub("", text)


def validate_text_input(text: str | None) -> ValidationResult:
    if text is None or text == "":
        return ValidationResult(False, "EMPTY_INPUT", "No reviews provided.")
    if not text.strip():
        return ValidationResult(False, "WHITESPACE_ONLY", "Input contains only whitespace.")

    if len(text) > MAX_PASTED_TEXT_LENGTH:
        return ValidationResult(
            False,
            "INPUT_TOO_LONG",
            f"Input exceeds the maximum length of {MAX_PASTED_TEXT_LENGTH:,} characters.",
        )

    without_emoji = _strip_emoji(text).strip()
    if not without_emoji:
        return ValidationResult(False, "EMOJI_ONLY", "Invalid input: only emoji were provided.")

    no_url = URL_RE.sub("", without_emoji).strip()
    if not no_url:
        return ValidationResult(False, "URL_ONLY", "Invalid input: only URLs were provided.")

    no_digits = DIGIT_RE.sub("", no_url)
    if not no_digits.strip():
        return ValidationResult(False, "NUMBER_ONLY", "Invalid input: only numbers were provided.")

    stripped_symbols = SYMBOL_RE.sub("", no_digits).strip()
    if not stripped_symbols:
        return ValidationResult(False, "SYMBOL_ONLY", "Invalid input: only symbols were provided.")

    if not ALPHA_RE.search(without_emoji):
        return ValidationResult(False, "NO_ALPHABETIC_CONTENT", "Invalid input: no readable text found.")

    return ValidationResult(True)


def validate_review_texts(texts: list[str]) -> ValidationResult:
    """Per-review length guard (spec section 12: extremely long reviews)."""
    for t in texts:
        if len(t) > MAX_REVIEW_LENGTH:
            return ValidationResult(
                False,
                "REVIEW_TOO_LONG",
                f"One or more reviews exceed the maximum length of {MAX_REVIEW_LENGTH:,} characters.",
            )
    return ValidationResult(True)
