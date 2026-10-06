"""Shared singletons wired through FastAPI dependencies."""
from __future__ import annotations

import threading
from functools import lru_cache

from config import MODELS_DIR
from ml.model_manager import ModelManager
from services.analysis_service import AnalysisPipeline, AnalysisStore


@lru_cache(maxsize=1)
def get_model_manager() -> ModelManager:
    return ModelManager(MODELS_DIR)


@lru_cache(maxsize=1)
def get_store() -> AnalysisStore:
    return AnalysisStore()


@lru_cache(maxsize=1)
def get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline(get_model_manager())


@lru_cache(maxsize=1)
def get_ask_service() -> "AskService":
    from services.ask_service import AskService

    return AskService()


@lru_cache(maxsize=1)
def get_product_store() -> "ProductStore":
    from services.product_store import ProductStore

    return ProductStore()


# CSV jobs run in background threads; a lock keeps store mutations safe.
store_lock = threading.Lock()
