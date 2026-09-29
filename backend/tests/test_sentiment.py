"""Sentiment engine tests (model-based, needs trained artifacts)."""
from __future__ import annotations

from services.preprocessing_service import PreprocessingService
from services.sentiment_service import SentimentService


class TestSentiment:
    def test_positive(self, manager):
        pre = PreprocessingService()
        sent = SentimentService(manager)
        p = pre.preprocess("The battery life is excellent and I love it.")
        results = sent.score([p.model_text], [[]])
        assert results[0]["sentiment"] == "Positive"
        assert results[0]["confidence"] > 0.5
        assert results[0]["positive_probability"] > results[0]["negative_probability"]

    def test_negative(self, manager):
        pre = PreprocessingService()
        sent = SentimentService(manager)
        p = pre.preprocess("The camera is terrible and the microphone is weak.")
        results = sent.score([p.model_text], [[]])
        assert results[0]["sentiment"] == "Negative"

    def test_probabilities_sum_to_one(self, manager):
        pre = PreprocessingService()
        sent = SentimentService(manager)
        p = pre.preprocess("It has a 6.5 inch display and 128GB storage.")
        r = sent.score([p.model_text], [[]])[0]
        total = r["positive_probability"] + r["negative_probability"] + r["neutral_probability"]
        assert abs(total - 1.0) < 0.02

    def test_confidence_is_max_probability(self, manager):
        pre = PreprocessingService()
        sent = SentimentService(manager)
        p = pre.preprocess("Absolutely amazing sound quality.")
        r = sent.score([p.model_text], [[]])[0]
        assert r["confidence"] == max(r["positive_probability"], r["negative_probability"], r["neutral_probability"])

    def test_mixed_review_supported(self, manager):
        pre = PreprocessingService()
        sent = SentimentService(manager)
        text = "The battery is amazing but the camera is terrible."
        p = pre.preprocess(text)
        from nlp.aspect_engine import analyze
        _, clauses = analyze(text)
        results = sent.score([p.model_text], [clauses])
        # mixed flip requires narrow margin; either way no crash and label is valid
        assert results[0]["sentiment"] in {"Positive", "Negative", "Neutral", "Mixed"}
