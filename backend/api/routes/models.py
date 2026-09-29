"""GET /api/models - model metadata + evaluation metrics from training.

New-format metadata (real-data pipeline): `candidates` are evaluated on the
VALIDATION set (used for model selection) and `selected_model_test_metrics`
holds the single held-out TEST evaluation.
Legacy metadata (synthetic v1): candidates were evaluated directly on the
test split, so the selected candidate doubles as the test evaluation.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_model_manager
from api.errors import ModelNotLoadedError
from ml.model_manager import ModelManager
from schemas.model import ClassMetrics, ModelEvaluation, ModelInfo, ModelsResponse

router = APIRouter()


def _to_evaluation(cand: dict) -> ModelEvaluation:
    return ModelEvaluation(
        model_name=cand["model_name"],
        accuracy=cand["accuracy"],
        precision_macro=cand["precision_macro"],
        recall_macro=cand["recall_macro"],
        macro_f1=cand["macro_f1"],
        weighted_f1=cand["weighted_f1"],
        per_class={
            cls: ClassMetrics(**vals)
            for cls, vals in cand.get("per_class", {}).items()
        },
        confusion_matrix=cand.get("confusion_matrix", []),
    )


@router.get("/models", response_model=ModelsResponse)
def get_models(manager: ModelManager = Depends(get_model_manager)):
    if not manager.loaded:
        raise ModelNotLoadedError(
            "MODELS_NOT_LOADED",
            "ML models are not loaded. Run the training scripts and restart the server.",
        )
    metadata = manager.metadata or {}
    models: list[ModelInfo] = []
    for task in ("sentiment", "review_detector"):
        meta = metadata.get(task)
        if not meta:
            continue
        # real-data format stores validation metrics under
        # "candidates_validation_metrics"; legacy format under "candidates"
        raw_candidates = meta.get("candidates_validation_metrics", meta.get("candidates", []))
        candidates = [_to_evaluation(cand) for cand in raw_candidates]

        if "selected_model_test_metrics" in meta:
            # real-data format
            test_raw = meta.get("selected_model_test_metrics")
            test_eval = _to_evaluation(test_raw) if test_raw else None
        else:
            # legacy synthetic format: candidates were evaluated on the test split
            test_eval = next(
                (c for c in candidates if c.model_name == meta.get("selected_model")),
                None,
            )

        models.append(ModelInfo(
            task=task,
            selected_model=meta.get("selected_model", "unknown"),
            selection_metric=meta.get("selection_metric", "macro_f1"),
            candidates=candidates,
            selected_model_test_metrics=test_eval,
            classes=meta.get("classes", []),
            training_rows=meta.get("training_rows", 0),
            validation_rows=meta.get("validation_rows"),
            test_rows=meta.get("test_rows", 0),
            tfidf_config=meta.get("tfidf_config", {}),
            training_dataset=meta.get("training_dataset", ""),
            dataset_name=meta.get("dataset_name"),
            dataset_size=meta.get("dataset_size"),
            class_distribution=meta.get("class_distribution"),
            imbalance_handling=meta.get("imbalance_handling"),
            trained_at=meta.get("trained_at", ""),
            model_version=meta.get("model_version", "1.0.0"),
        ))
    return ModelsResponse(models=models)
