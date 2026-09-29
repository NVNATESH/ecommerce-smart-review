"""Trains the 3-class sentiment model (Negative / Neutral / Positive).

* TF-IDF features over the same preprocessing used at inference time.
* Candidates: Multinomial Naive Bayes, Logistic Regression, calibrated LR.
* Model selection metric: MACRO F1 (never accuracy alone).
* Stratified split; no leakage - the test set is only touched for evaluation.
* Saves artifacts + metadata.json consumed by GET /api/models.

Usage:
    python training/train_sentiment.py
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DATA_DIR, MODELS_DIR  # noqa: E402
from nlp.preprocessing import TextPreprocessor  # noqa: E402

SEED = 42
TFIDF_CONFIG = {
    "analyzer": "word",
    "ngram_range": [1, 2],
    "min_df": 2,
    "max_df": 0.95,
    "sublinear_tf": True,
    "strip_accents": "unicode",
}


def evaluate(name: str, model, X_test, y_test, classes: list[str]) -> dict:
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="macro", zero_division=0,
    )
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    per_class_vals = precision_recall_fscore_support(
        y_test, y_pred, labels=classes, zero_division=0,
    )
    per_class = {
        cls: {
            "precision": round(float(per_class_vals[0][i]), 4),
            "recall": round(float(per_class_vals[1][i]), 4),
            "f1_score": round(float(per_class_vals[2][i]), 4),
            "support": int(per_class_vals[3][i]),
        }
        for i, cls in enumerate(classes)
    }
    cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()
    print(f"  {name:<28} acc={acc:.4f} macro_f1={macro_f1:.4f} weighted_f1={weighted_f1:.4f}")
    return {
        "model_name": name,
        "accuracy": round(float(acc), 4),
        "precision_macro": round(float(macro_p), 4),
        "recall_macro": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "per_class": per_class,
        "confusion_matrix": cm,
    }


def main() -> None:
    print("== Sentiment model training ==")
    df = pd.read_csv(DATA_DIR / "processed" / "train_sentiment.csv")
    df = df.dropna().drop_duplicates(subset=["review"])
    print(f"Training rows: {len(df)}; class counts:\n{df['sentiment'].value_counts().to_string()}")

    preprocessor = TextPreprocessor()
    texts = [preprocessor.preprocess(t).model_text for t in df["review"].astype(str)]
    labels = df["sentiment"].astype(str).tolist()
    classes = sorted(set(labels))

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, stratify=labels, random_state=SEED,
    )

    vectorizer = TfidfVectorizer(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in TFIDF_CONFIG.items()})
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)  # transform only - no leakage

    candidates = {
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.5),
        "Logistic Regression": LogisticRegression(
            C=4.0, max_iter=2000, class_weight="balanced", random_state=SEED,
        ),
        "Calibrated Logistic Regression": CalibratedClassifierCV(
            LogisticRegression(C=4.0, max_iter=2000, class_weight="balanced", random_state=SEED),
            method="sigmoid", cv=3,
        ),
    }

    results = []
    fitted = {}
    for name, model in candidates.items():
        t0 = time.perf_counter()
        model.fit(X_train_vec, y_train)
        fitted[name] = model
        results.append(evaluate(name, model, X_test_vec, y_test, classes))
        print(f"    ({time.perf_counter() - t0:.1f}s)")

    best = max(results, key=lambda r: r["macro_f1"])
    print(f"Selected (macro F1): {best['model_name']}")

    joblib.dump(fitted[best["model_name"]], MODELS_DIR / "sentiment_model.pkl")
    joblib.dump(vectorizer, MODELS_DIR / "sentiment_vectorizer.pkl")

    metadata_path = MODELS_DIR / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    metadata["sentiment"] = {
        "selected_model": best["model_name"],
        "selection_metric": "macro_f1",
        "classes": classes,
        "training_rows": len(X_train),
        "test_rows": len(X_test),
        "tfidf_config": TFIDF_CONFIG,
        "training_dataset": "data/processed/train_sentiment.csv",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_version": "1.0.0",
        "candidates": results,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("Saved artifacts + metadata.")


if __name__ == "__main__":
    main()
