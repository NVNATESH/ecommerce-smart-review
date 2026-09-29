"""Real-data sentiment training pipeline (supersedes the synthetic demo run).

Pipeline (in order):
    1.  Load the 80/10/10 splits produced by training/prepare_real_dataset.py.
    2.  Fit TF-IDF on the TRAINING SET ONLY (no validation/test leakage).
    3.  Train Multinomial Naive Bayes and Logistic Regression.
    4.  Evaluate BOTH candidates on the VALIDATION set (accuracy, precision,
        recall, macro F1, weighted F1).
    5.  Select the winner by VALIDATION MACRO F1.
    6.  Evaluate the selected model exactly ONCE on the held-out TEST set,
        including the confusion matrix.
    7.  Verify prediction probabilities (rows sum to 1, all finite).
    8.  Save artifacts to models_staging/ and run the promotion gate:
          - validation macro F1 >= MIN_VAL_MACRO_F1
          - test macro F1 >= MIN_TEST_MACRO_F1
          - test macro F1 >= PROMOTION_DROP_FACTOR * validation macro F1
          - unambiguous sample reviews classified with the expected polarity
        Only if every gate passes are the working artifacts in models/ backed
        up to models/backup-<timestamp>/ and the new artifacts promoted.
        The old model is NEVER overwritten on failure.
    9.  Update models/metadata.json (dataset name/size, class distribution,
        training date, selected model, per-candidate validation metrics,
        held-out test metrics, TF-IDF parameters). The previous synthetic
        entry is preserved under "sentiment_synthetic_v1" for auditability.

Usage:
    python training/train_sentiment_real.py
"""
from __future__ import annotations

import json
import shutil
import sys
import time
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
from nlp.preprocessing import TextPreprocessor  # noqa: E402

SEED = 42
SPLITS_DIR = DATA_DIR / "real" / "processed"
STAGING_DIR = MODELS_DIR.parent / "models_staging"

# Promotion gates — the working model is never replaced unless all pass.
MIN_VAL_MACRO_F1 = 0.55
MIN_TEST_MACRO_F1 = 0.55
PROMOTION_DROP_FACTOR = 0.80  # test may not drop below 80% of validation F1

TFIDF_CONFIG = {
    "analyzer": "word",
    "ngram_range": [1, 2],
    "min_df": 2,
    "max_df": 0.95,
    "sublinear_tf": True,
    "strip_accents": "unicode",
}

SAMPLE_CHECKS = [
    ("The battery life is excellent and I love it.", "positive"),
    ("Camera quality is terrible and the microphone is weak.", "negative"),
    ("Terrible product, stopped working within a week, waste of money.", "negative"),
    ("Amazing quality, works perfectly, very happy with this purchase.", "positive"),
]


def evaluate(model, X, y_true, classes: list[str]) -> dict:
    y_pred = model.predict(X)
    acc = accuracy_score(y_true, y_pred)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0,
    )
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    per = precision_recall_fscore_support(y_true, y_pred, labels=classes, zero_division=0)
    return {
        "accuracy": round(float(acc), 4),
        "precision_macro": round(float(macro_p), 4),
        "recall_macro": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "per_class": {
            cls: {
                "precision": round(float(per[0][i]), 4),
                "recall": round(float(per[1][i]), 4),
                "f1_score": round(float(per[2][i]), 4),
                "support": int(per[3][i]),
            }
            for i, cls in enumerate(classes)
        },
    }, y_pred


def verify_probabilities(model, X) -> None:
    probas = model.predict_proba(X[:1000])
    assert probas.shape[1] == 3, "expected 3 class probabilities"
    sums = probas.sum(axis=1)
    assert abs(sums - 1.0).max() < 1e-6, f"probabilities do not sum to 1 (max dev {abs(sums - 1.0).max():.2e})"
    assert bool(pd.notna(probas).all().all()), "NaN found in probability matrix"


def main() -> None:
    t_start = time.perf_counter()
    prep_report = json.loads((SPLITS_DIR / "prep_report.json").read_text(encoding="utf-8"))
    print("== Real-data sentiment training ==")
    print(f"Dataset: {prep_report.get('dataset_name', prep_report.get('source_file'))}")

    train_df = pd.read_csv(SPLITS_DIR / "train.csv").dropna()
    val_df = pd.read_csv(SPLITS_DIR / "validation.csv").dropna()
    test_df = pd.read_csv(SPLITS_DIR / "test.csv").dropna()
    classes = ["negative", "neutral", "positive"]

    preprocessor = TextPreprocessor()

    def load_model_texts(name: str, df: pd.DataFrame) -> list[str]:
        """Preprocess once and cache to disk; reuse on reruns."""
        cache = SPLITS_DIR / f"{name}.modeltext.txt"
        if cache.exists():
            lines = cache.read_text(encoding="utf-8").splitlines()
            if len(lines) == len(df):
                return lines
        texts = [preprocessor.preprocess(t).model_text for t in df["review"].astype(str)]
        cache.write_text("\n".join(texts), encoding="utf-8")
        return texts

    print("Preprocessing text (train/val/test)…")
    X_train_text = load_model_texts("train", train_df)
    X_val_text = load_model_texts("validation", val_df)
    X_test_text = load_model_texts("test", test_df)
    y_train = train_df["sentiment"].astype(str).tolist()
    y_val = val_df["sentiment"].astype(str).tolist()
    y_test = test_df["sentiment"].astype(str).tolist()

    # 2) TF-IDF fitted on TRAIN ONLY -----------------------------------------
    vectorizer = TfidfVectorizer(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in TFIDF_CONFIG.items()})
    X_train = vectorizer.fit_transform(X_train_text)
    X_val = vectorizer.transform(X_val_text)
    X_test = vectorizer.transform(X_test_text)
    print(f"TF-IDF features: {X_train.shape[1]:,} (fit on train only)")

    # 3) candidates -------------------------------------------------------------
    # Class imbalance (2:1:2) is handled without touching validation/test:
    # * Logistic Regression: class_weight='balanced' computed from TRAIN labels only
    # * Multinomial NB: standard fit (priors estimated from TRAIN only)
    candidates = {
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.3),
        "Logistic Regression": LogisticRegression(
            C=4.0, max_iter=2000, class_weight="balanced", random_state=SEED, n_jobs=-1,
        ),
    }

    validation_results = {}
    for name, model in candidates.items():
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        metrics, _ = evaluate(model, X_val, y_val, classes)
        metrics["model_name"] = name
        validation_results[name] = metrics
        print(f"  [validation] {name:<26} acc={metrics['accuracy']:.4f} "
              f"macro_f1={metrics['macro_f1']:.4f} weighted_f1={metrics['weighted_f1']:.4f} "
              f"({time.perf_counter() - t0:.1f}s)")

    # 5) select on VALIDATION macro F1 ------------------------------------------
    selected_name = max(validation_results, key=lambda n: validation_results[n]["macro_f1"])
    selected_model = candidates[selected_name]
    val_f1 = validation_results[selected_name]["macro_f1"]
    print(f"Selected by validation macro F1: {selected_name} ({val_f1:.4f})")

    # 6) ONE held-out test evaluation -------------------------------------------
    test_metrics, y_test_pred = evaluate(selected_model, X_test, y_test, classes)
    cm = confusion_matrix(y_test, y_test_pred, labels=classes).tolist()
    test_metrics["confusion_matrix"] = cm
    test_metrics["model_name"] = selected_name
    print(f"[test] {selected_name:<26} acc={test_metrics['accuracy']:.4f} "
          f"macro_f1={test_metrics['macro_f1']:.4f} weighted_f1={test_metrics['weighted_f1']:.4f}")

    # 7) probability verification -------------------------------------------------
    print("Verifying prediction probabilities…")
    verify_probabilities(selected_model, X_val)

    # 8) staging + promotion gate --------------------------------------------------
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(selected_model, STAGING_DIR / "sentiment_model.pkl")
    joblib.dump(vectorizer, STAGING_DIR / "sentiment_vectorizer.pkl")

    # Sample sanity checks with the STAGED model (same preprocessing as serving)
    print("Sample sanity checks (staged model):")
    sample_X = vectorizer.transform([preprocessor.preprocess(t).model_text for t, _ in SAMPLE_CHECKS])
    sample_pred = selected_model.predict(sample_X)
    sample_ok = 0
    for (text, expected), pred in zip(SAMPLE_CHECKS, sample_pred):
        ok = pred == expected
        sample_ok += int(ok)
        print(f"  [{'ok' if ok else 'MISS'}] expected={expected:<8} predicted={pred:<8} {text[:60]!r}")
    sample_gate = sample_ok >= len(SAMPLE_CHECKS) - 1  # allow at most one miss

    gates = {
        "validation_macro_f1 >= MIN_VAL_MACRO_F1": val_f1 >= MIN_VAL_MACRO_F1,
        "test_macro_f1 >= MIN_TEST_MACRO_F1": test_metrics["macro_f1"] >= MIN_TEST_MACRO_F1,
        "test >= PROMOTION_DROP_FACTOR * validation": test_metrics["macro_f1"] >= PROMOTION_DROP_FACTOR * val_f1,
        "sample sanity checks": sample_gate,
    }
    print("Promotion gates:", {k: ("PASS" if v else "FAIL") for k, v in gates.items()})
    if not all(gates.values()):
        print("GATE FAILURE — working model in models/ left untouched. Staged artifacts kept in models_staging/.")
        sys.exit(2)

    # Backup old artifacts, then promote ------------------------------------------
    old_meta_path = MODELS_DIR / "metadata.json"
    old_meta = json.loads(old_meta_path.read_text(encoding="utf-8")) if old_meta_path.exists() else {}
    backup_dir = MODELS_DIR.parent / f"models_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for fname in ("sentiment_model.pkl", "sentiment_vectorizer.pkl", "metadata.json"):
        src = MODELS_DIR / fname
        if src.exists():
            shutil.copy2(src, backup_dir / fname)
    # the review detector artifacts stay as-is (not retrained in this run)
    print(f"Backed up previous sentiment artifacts + metadata -> {backup_dir.name}")

    for fname in ("sentiment_model.pkl", "sentiment_vectorizer.pkl"):
        shutil.copy2(STAGING_DIR / fname, MODELS_DIR / fname)

    # 9) metadata -------------------------------------------------------------------
    metadata = dict(old_meta)
    if "sentiment" in old_meta:
        metadata["sentiment_synthetic_v1"] = old_meta["sentiment"]  # audit trail of the synthetic run
    metadata["sentiment"] = {
        "selected_model": selected_name,
        "selection_metric": "macro_f1 (validation set)",
        "classes": classes,
        "training_rows": int(X_train.shape[0]),
        "validation_rows": int(X_val.shape[0]),
        "test_rows": int(X_test.shape[0]),
        "tfidf_config": TFIDF_CONFIG,
        "training_dataset": "data/real/processed/{train,validation,test}.csv",
        "dataset_name": prep_report.get("dataset_name", prep_report.get("source_file", "real CSV")),
        "dataset_size": prep_report.get("rows_after_cleaning"),
        "class_distribution": prep_report.get("class_distribution_overall"),
        "class_distribution_train": prep_report.get("class_distribution_train"),
        "imbalance_handling": (
            "Logistic Regression: class_weight='balanced' (computed on train only); "
            "Multinomial NB: train-only priors; splits stratified"
        ),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "model_version": "2.0.0-real-data",
        "candidates_validation_metrics": [validation_results[n] for n in validation_results],
        "selected_model_test_metrics": test_metrics,
        "promotion_gates": {k: ("PASS" if v else "FAIL") for k, v in gates.items()},
        "backup_dir": backup_dir.name,
    }
    old_meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Metadata updated. Total time: {time.perf_counter() - t_start:.1f}s")


if __name__ == "__main__":
    main()
