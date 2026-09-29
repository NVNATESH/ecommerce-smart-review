"""Review detector: Review vs Not Review (TF-IDF char n-grams + Logistic Regression).

Character n-grams are used deliberately: they capture the surface shape of
non-review text (URLs, digit strings, symbol spam) better than word n-grams.
"""
from __future__ import annotations

import numpy as np


class ReviewDetector:
    VALID_THRESHOLD = 0.80   # >80% -> VALID
    INVALID_THRESHOLD = 0.20  # <20% -> INVALID; between -> UNCERTAIN

    def __init__(self, model, vectorizer):
        self.model = model
        self.vectorizer = vectorizer
        self.classes = [str(c) for c in getattr(model, "classes_", ["Not Review", "Review"])]

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, len(self.classes)))
        X = self.vectorizer.transform(texts)
        return self.model.predict_proba(X)

    @staticmethod
    def review_probability(proba_row: np.ndarray, classes: list[str]) -> float:
        for i, c in enumerate(classes):
            if c.lower() == "review":
                return float(proba_row[i])
        return float(proba_row[-1])

    @classmethod
    def status_for(cls, review_probability: float) -> str:
        if review_probability > cls.VALID_THRESHOLD:
            return "VALID"
        if review_probability < cls.INVALID_THRESHOLD:
            return "INVALID"
        return "UNCERTAIN"
