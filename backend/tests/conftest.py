"""Shared pytest fixtures. Tests use small deterministic inputs; models must
be trained first (see README). Tests that need artifacts are skipped with a
clear message otherwise."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from config import MODELS_DIR  # noqa: E402
from ml.model_manager import ModelManager  # noqa: E402


@pytest.fixture(scope="session")
def manager():
    mgr = ModelManager(MODELS_DIR)
    if not all(
        (MODELS_DIR / f).exists()
        for f in (
            "sentiment_model.pkl", "sentiment_vectorizer.pkl",
            "review_detector.pkl", "review_detector_vectorizer.pkl",
        )
    ):
        pytest.skip("Model artifacts missing - run training scripts first.")
    mgr.load()
    return mgr
