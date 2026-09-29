"""Prediction explanation for the Review Inspector."""
from __future__ import annotations

from nlp.keyword_extractor import top_contributing_terms


def explain_prediction(
    text: str,
    vectorizer,
    model,
    class_label: str,
    classes: list[str],
    k: int = 6,
    feature_names=None,
) -> list[str]:
    """Model features that contributed strongly to the classification.

    The wording used in the product is intentionally non-causal: these are
    contributing model features, not proof of why the review says what it says.
    """
    if class_label not in classes:
        return []
    return top_contributing_terms(
        text, vectorizer, model, classes.index(class_label), k=k,
        feature_names=feature_names,
    )
