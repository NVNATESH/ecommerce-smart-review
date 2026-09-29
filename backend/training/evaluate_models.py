"""Re-evaluates the saved model artifacts on a fresh stratified split.

Useful for a quick health check of the deployed artifacts.

Usage:
    python training/evaluate_models.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DATA_DIR, MODELS_DIR  # noqa: E402
from nlp.preprocessing import TextPreprocessor  # noqa: E402

SEED = 42


def main() -> None:
    preprocessor = TextPreprocessor()
    print("== Sentiment ==")
    df = pd.read_csv(DATA_DIR / "processed" / "train_sentiment.csv").dropna()
    texts = [preprocessor.preprocess(t).model_text for t in df["review"].astype(str)]
    labels = df["sentiment"].astype(str).tolist()
    _, X_test, _, y_test = train_test_split(texts, labels, test_size=0.2, stratify=labels, random_state=SEED)
    vec = joblib.load(MODELS_DIR / "sentiment_vectorizer.pkl")
    model = joblib.load(MODELS_DIR / "sentiment_model.pkl")
    y_pred = model.predict(vec.transform(X_test))
    print(f"accuracy={accuracy_score(y_test, y_pred):.4f} macro_f1={f1_score(y_test, y_pred, average='macro'):.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))

    print("== Review detector ==")
    df = pd.read_csv(DATA_DIR / "processed" / "train_review_detector.csv").dropna()
    texts = df["text"].astype(str).tolist()
    labels = df["label"].astype(str).tolist()
    _, X_test, _, y_test = train_test_split(texts, labels, test_size=0.2, stratify=labels, random_state=SEED)
    vec = joblib.load(MODELS_DIR / "review_detector_vectorizer.pkl")
    model = joblib.load(MODELS_DIR / "review_detector.pkl")
    y_pred = model.predict(vec.transform(X_test))
    print(f"accuracy={accuracy_score(y_test, y_pred):.4f} macro_f1={f1_score(y_test, y_pred, average='macro'):.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))


if __name__ == "__main__":
    main()
