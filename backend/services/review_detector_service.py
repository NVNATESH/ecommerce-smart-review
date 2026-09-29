"""Review detector service: Review vs Not Review probabilities + status."""
from __future__ import annotations

from ml.model_manager import ModelManager
from ml.review_detector import ReviewDetector


class ReviewDetectorService:
    def __init__(self, manager: ModelManager):
        self.detector = ReviewDetector(manager.review_detector, manager.review_detector_vectorizer)

    def score(self, original_texts: list[str]) -> list[dict]:
        """One record per input text:
        {review_probability, not_review_probability, review_status}.

        UNCERTAIN (20-80%) is kept as its own status - uncertain data is never
        silently forced into valid or invalid.
        """
        probas = self.detector.predict_proba(original_texts)
        results = []
        for row in probas:
            p_review = ReviewDetector.review_probability(row, self.detector.classes)
            results.append({
                "review_probability": round(float(p_review), 4),
                "not_review_probability": round(float(1.0 - p_review), 4),
                "review_status": ReviewDetector.status_for(p_review),
            })
        return results
