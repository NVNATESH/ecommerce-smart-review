"""Model metadata / metrics schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ClassMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    support: int


class ModelEvaluation(BaseModel):
    model_name: str
    accuracy: float
    precision_macro: float
    recall_macro: float
    macro_f1: float
    weighted_f1: float
    per_class: dict[str, ClassMetrics]
    confusion_matrix: list[list[int]]


class ModelInfo(BaseModel):
    task: str  # "sentiment" | "review_detection"
    selected_model: str
    selection_metric: str  # e.g. "macro_f1 (validation set)"
    candidates: list[ModelEvaluation]  # evaluated on the validation set
    selected_model_test_metrics: ModelEvaluation | None = None  # one held-out test evaluation
    classes: list[str]
    training_rows: int
    validation_rows: int | None = None
    test_rows: int
    tfidf_config: dict[str, Any]
    training_dataset: str
    dataset_name: str | None = None
    dataset_size: int | None = None
    class_distribution: dict[str, int] | None = None
    imbalance_handling: str | None = None
    trained_at: str
    model_version: str


class ModelsResponse(BaseModel):
    success: bool = True
    models: list[ModelInfo]
