"""Term-level explainability for TF-IDF + linear models and simple stats."""
from __future__ import annotations

import numpy as np
from scipy import sparse  # noqa: F401  (numpy/scipy come with scikit-learn)


def top_contributing_terms(
    text: str,
    vectorizer,
    model,
    class_index: int | None,
    k: int = 6,
    feature_names: np.ndarray | list[str] | None = None,
) -> list[str]:
    """Return the model features that contributed most to a classification.

    For linear models this is feature_value * coefficient for the predicted
    class. This is a model-attribution view, not a causal explanation.
    `feature_names` may be precomputed once per vectorizer (building it is
    expensive for large vocabularies) — pass it from the pipeline hot path.
    """
    try:
        row = vectorizer.transform([text])
        if row.nnz == 0:
            return []
        if feature_names is None:
            feature_names = vectorizer.get_feature_names_out()

        if hasattr(model, "coef_"):
            coefs = model.coef_
            if coefs.shape[0] == 1:  # binary
                coef = coefs[0] if class_index in (0, None) else -coefs[0]
            else:
                coef = coefs[class_index if class_index is not None else 0]
            contributions = row.multiply(coef).toarray()[0]
        elif hasattr(model, "feature_log_prob_"):
            log_probs = model.feature_log_prob_
            lp = log_probs[class_index if class_index is not None else 0]
            contributions = row.multiply(lp - lp.mean()).toarray()[0]
        else:
            return []

        nz = contributions.nonzero()[0]
        if len(nz) == 0:
            return []
        order = nz[np.argsort(np.abs(contributions[nz]))[::-1]]
        terms = [feature_names[i] for i in order[:k]]
        return [t for t in terms if t.strip()]
    except Exception:
        return []


def vocabulary_richness(texts: list[str]) -> float:
    """Type/token ratio across a dataset (dataset diversity signal)."""
    tokens: list[str] = []
    for t in texts:
        tokens.extend(t.lower().split())
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)
