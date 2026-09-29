"""Preprocessing service: batches raw review text through the NLTK pipeline."""
from __future__ import annotations

from nlp.preprocessing import PreprocessedText, TextPreprocessor


class PreprocessingService:
    """Instantiated once per application; the underlying processor is stateless."""

    def __init__(self) -> None:
        self.processor = TextPreprocessor()

    def preprocess(self, text: str):
        return self.processor.preprocess(text)

    def preprocess_batch(self, texts: list[str]) -> list[PreprocessedText]:
        return self.processor.preprocess_batch(texts)
