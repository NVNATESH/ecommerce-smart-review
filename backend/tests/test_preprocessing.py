"""Preprocessing tests: numbers, negation, repetitions, three text forms."""
from __future__ import annotations

import pytest

from nlp.preprocessing import TextPreprocessor


@pytest.fixture(scope="module")
def processor():
    return TextPreprocessor()


class TestPreprocessing:
    def test_three_forms(self, processor):
        result = processor.preprocess("The battery is GOOOOOD!!!")
        assert result.original_text == "The battery is GOOOOOD!!!"
        assert "good" in result.normalized_text.lower()
        assert "good" in result.model_text
        assert result.normalized_text != result.original_text

    def test_preserves_meaningful_numbers(self, processor):
        result = processor.preprocess("It has a 5000mAh battery and 120Hz screen for ₹20000.")
        model = result.model_text
        assert "5000mah" in model
        assert "120hz" in model
        assert "20000" in model

    def test_preserves_negation(self, processor):
        result = processor.preprocess("This is not good at all.")
        assert "not_good" in result.model_text

    def test_never_works_negation(self, processor):
        result = processor.preprocess("It never works properly.")
        assert any(t.startswith("not_") for t in result.tokens)

    def test_repeated_chars_collapsed(self, processor):
        result = processor.preprocess("The sound is amaaaazing")
        assert "amaazing" in result.normalized_text
        # model form de-duplicates the exaggerated run (lemma of "amazing")
        assert "amaz" in result.model_text and "amaa" not in result.model_text

    def test_emoji_captured(self, processor):
        result = processor.preprocess("Great phone 😀😀")
        assert result.emojis

    def test_word_count(self, processor):
        result = processor.preprocess("The battery is excellent and the display is bright.")
        assert result.word_count == 9

    def test_alphabetic_and_symbol_ratios(self, processor):
        result = processor.preprocess("asd123###")
        assert result.alphabetic_ratio < 0.5
        assert result.symbol_ratio > 0.2

    def test_urls_removed(self, processor):
        result = processor.preprocess("Check https://example.com for details")
        assert "example.com" not in result.normalized_text
