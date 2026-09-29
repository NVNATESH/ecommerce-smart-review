"""Input validation + input service tests (spec section 67)."""
from __future__ import annotations

import io

import pandas as pd
import pytest

from api.errors import InvalidCSVError
from services.input_service import detect_review_column, parse_pasted_text
from validation.input_validator import validate_text_input


class TestInputValidation:
    def test_empty(self):
        assert validate_text_input("").valid is False
        assert validate_text_input("").code == "EMPTY_INPUT"

    def test_whitespace_only(self):
        assert validate_text_input("   \n\t  ").code == "WHITESPACE_ONLY"

    def test_emoji_only(self):
        result = validate_text_input("😀😀😀😀")
        assert result.valid is False
        assert result.code == "EMOJI_ONLY"

    def test_number_only(self):
        assert validate_text_input("123456789").code == "NUMBER_ONLY"

    def test_symbol_only(self):
        assert validate_text_input("$$$$$$$$").code == "SYMBOL_ONLY"

    def test_url_only(self):
        assert validate_text_input("https://example.com").code == "URL_ONLY"

    def test_valid_review(self):
        assert validate_text_input("The battery life is excellent.").valid is True

    def test_emoji_with_text_is_valid(self):
        assert validate_text_input("Great phone! 😀").valid is True


class TestParsePastedText:
    def test_splits_lines(self):
        reviews = parse_pasted_text("Battery is great.\nCamera is terrible.")
        assert len(reviews) == 2

    def test_splits_paragraphs(self):
        reviews = parse_pasted_text("Battery is great.\n\nCamera is terrible.")
        assert len(reviews) == 2

    def test_rejects_invalid(self):
        with pytest.raises(Exception):
            parse_pasted_text("")

    def test_minimum_reviews_enforced_downstream(self):
        # <3 reviews must lead to a dataset REJECT decision (covered in quality tests)
        assert len(parse_pasted_text("Good phone.\nNice screen.")) == 2


class TestColumnDetection:
    def test_exact_match_priority(self):
        cols = ["id", "comment", "review", "text"]
        assert detect_review_column(cols) == "review"

    def test_partial_match(self):
        assert detect_review_column(["id", "my_review_text"]) == "my_review_text"

    def test_no_match(self):
        assert detect_review_column(["id", "name", "price"]) is None


class TestCSVParsing:
    def _csv(self, rows: dict) -> bytes:
        buf = io.StringIO()
        pd.DataFrame(rows).to_csv(buf, index=False)
        return buf.getvalue().encode("utf-8")

    def test_valid_csv(self):
        content = self._csv({"review": ["Great battery.", "Bad camera."], "rating": [5, 1]})
        reviews = parse_csv(content, "reviews.csv")
        assert len(reviews) == 2

    def test_missing_column(self):
        content = self._csv({"name": ["a"], "price": [1]})
        with pytest.raises(InvalidCSVError) as exc:
            parse_csv(content, "bad.csv")
        assert exc.value.code == "REVIEW_COLUMN_NOT_FOUND"

    def test_malformed_csv(self):
        with pytest.raises(InvalidCSVError):
            parse_csv(b"\x00\x01\x02 not a csv at all", "x.csv")

    def test_wrong_extension(self):
        from api.errors import FileSecurityError

        with pytest.raises(FileSecurityError):
            parse_csv(b"a,b\n1,2", "data.exe")


def parse_csv(content: bytes, filename: str):
    from services.input_service import parse_csv_upload

    return parse_csv_upload(filename, len(content), content[:8], content)
