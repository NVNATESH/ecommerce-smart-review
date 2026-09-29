"""Sentiment engine: TF-IDF -> trained classifier with class probabilities."""
from __future__ import annotations

import numpy as np


class SentimentEngine:
    """Wraps the trained sentiment pipeline (vectorizer + classifier).

    The vectorizer is applied to the `model_text` representation produced by
    TextPreprocessor (lower-cased, negation-joined, lemmatised) so training
    and inference see identical distributions.
    """

    CLASSES = ["Negative", "Neutral", "Positive"]

    def __init__(self, model, vectorizer):
        self.model = model
        self.vectorizer = vectorizer
        classes = [str(c) for c in getattr(model, "classes_", self.CLASSES)]
        # normalize class names to our canonical labels
        self.classes = [c.capitalize() if c.capitalize() in self.CLASSES else c for c in classes]

    def predict_proba(self, model_texts: list[str]) -> np.ndarray:
        if not model_texts:
            return np.zeros((0, len(self.classes)))
        X = self.vectorizer.transform(model_texts)
        return self.model.predict_proba(X)

    def class_index(self, label: str) -> int:
        try:
            return self.classes.index(label)
        except ValueError:
            return 0
