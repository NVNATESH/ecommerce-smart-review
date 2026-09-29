"""ModelManager: loads every artifact once at startup and reuses it for requests."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib

logger = logging.getLogger("app.models")

ARTIFACTS = {
    "sentiment_model": "sentiment_model.pkl",
    "sentiment_vectorizer": "sentiment_vectorizer.pkl",
    "review_detector": "review_detector.pkl",
    "review_detector_vectorizer": "review_detector_vectorizer.pkl",
}


class ModelManager:
    def __init__(self, models_dir: Path):
        self.models_dir = Path(models_dir)
        self.sentiment_model = None
        self.sentiment_vectorizer = None
        self.review_detector = None
        self.review_detector_vectorizer = None
        self.metadata: dict = {}
        self.loaded = False

    def load(self) -> None:
        missing = [
            name for name, fname in ARTIFACTS.items()
            if not (self.models_dir / fname).exists()
        ]
        if missing:
            raise FileNotFoundError(
                f"Missing model artifacts: {', '.join(missing)}. "
                "Run `python training/train_sentiment.py` and "
                "`python training/train_review_detector.py` first."
            )
        for name, fname in ARTIFACTS.items():
            setattr(self, name, joblib.load(self.models_dir / fname))
        meta_path = self.models_dir / "metadata.json"
        if meta_path.exists():
            self.metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        self.loaded = True
        logger.info(
            "Models loaded from %s (sentiment=%s, review_detector=%s)",
            self.models_dir.name,
            self.metadata.get("sentiment", {}).get("selected_model", "?"),
            self.metadata.get("review_detector", {}).get("selected_model", "?"),
        )

    def __bool__(self) -> bool:  # convenience for dependency checks
        return self.loaded
