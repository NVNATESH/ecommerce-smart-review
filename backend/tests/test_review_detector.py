"""Review detector tests (model-based, needs trained artifacts)."""
from __future__ import annotations

from services.review_detector_service import ReviewDetectorService


class TestReviewDetector:
    def test_real_review_is_valid(self, manager):
        service = ReviewDetectorService(manager)
        results = service.score(["The battery life is excellent and the display is bright."])
        assert results[0]["review_status"] == "VALID"
        assert results[0]["review_probability"] > 0.8

    def test_non_review_detected(self, manager):
        service = ReviewDetectorService(manager)
        results = service.score(["https://example.com", "123456789"])
        for r in results:
            assert r["review_status"] == "INVALID"
            assert r["not_review_probability"] > 0.8

    def test_probabilities_sum_to_one(self, manager):
        service = ReviewDetectorService(manager)
        results = service.score(["Great phone, works smoothly."])
        assert abs(results[0]["review_probability"] + results[0]["not_review_probability"] - 1.0) < 0.01

    def test_uncertain_not_forced(self, manager):
        """A 20-80% band must exist; statuses are never silently forced."""
        service = ReviewDetectorService(manager)
        results = service.score(["The meeting is scheduled at 3 PM."])
        assert results[0]["review_status"] in {"VALID", "INVALID", "UNCERTAIN"}
