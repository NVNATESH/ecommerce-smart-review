"""Trains the Review vs Not Review detector.

TF-IDF character n-grams (3-5) + Logistic Regression; selected on MACRO F1
against a Multinomial Naive Bayes candidate.

Usage:
    python training/train_review_detector.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
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

SEED = 42
TFIDF_CONFIG = {
    "analyzer": "char_wb",
    "ngram_range": [3, 5],
    "min_df": 2,
    "sublinear_tf": True,
}


def evaluate(name, model, X_test, y_test, classes) -> dict:
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="macro", zero_division=0,
    )
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    per_class_vals = precision_recall_fscore_support(y_test, y_pred, labels=classes, zero_division=0)
    per_class = {
        cls: {
            "precision": round(float(per_class_vals[0][i]), 4),
            "recall": round(float(per_class_vals[1][i]), 4),
            "f1_score": round(float(per_class_vals[2][i]), 4),
            "support": int(per_class_vals[3][i]),
        }
        for i, cls in enumerate(classes)
    }
    print(f"  {name:<28} acc={acc:.4f} macro_f1={macro_f1:.4f} weighted_f1={weighted_f1:.4f}")
    return {
        "model_name": name,
        "accuracy": round(float(acc), 4),
        "precision_macro": round(float(macro_p), 4),
        "recall_macro": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=classes).tolist(),
    }


def main() -> None:
    print("== Review detector training ==")
    df = pd.read_csv(DATA_DIR / "processed" / "train_review_detector.csv")
    df = df.dropna().drop_duplicates(subset=["text"])
    print(f"Training rows: {len(df)}; class counts:\n{df['label'].value_counts().to_string()}")

    texts = df["text"].astype(str).tolist()
    labels = df["label"].astype(str).tolist()
    classes = sorted(set(labels))

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, stratify=labels, random_state=SEED,
    )

    vectorizer = TfidfVectorizer(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in TFIDF_CONFIG.items()})
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    candidates = {
        "Logistic Regression": LogisticRegression(
            C=8.0, max_iter=2000, class_weight="balanced", random_state=SEED,
        ),
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.3),
    }

    results, fitted = [], {}
    for name, model in candidates.items():
        model.fit(X_train_vec, y_train)
        fitted[name] = model
        results.append(evaluate(name, model, X_test_vec, y_test, classes))

    best = max(results, key=lambda r: r["macro_f1"])
    print(f"Selected (macro F1): {best['model_name']}")

    joblib.dump(fitted[best["model_name"]], MODELS_DIR / "review_detector.pkl")
    joblib.dump(vectorizer, MODELS_DIR / "review_detector_vectorizer.pkl")

    metadata_path = MODELS_DIR / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    metadata["review_detector"] = {
        "selected_model": best["model_name"],
        "selection_metric": "macro_f1",
        "classes": classes,
        "training_rows": len(X_train),
        "test_rows": len(X_test),
        "tfidf_config": TFIDF_CONFIG,
        "training_dataset": "data/processed/train_review_detector.csv",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_version": "1.0.0",
        "candidates": results,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("Saved artifacts + metadata.")


if __name__ == "__main__":
    main()
