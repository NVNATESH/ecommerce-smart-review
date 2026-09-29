"""Tests the currently deployed sentiment model against backend/data/sample_reviews.csv.

Reports predicted label + probabilities per row. Informational: the sample
file mixes garbage/URL/emoji/non-review rows on purpose, so only rows with an
unambiguous sentiment seed are hard-checked.

Usage:
    python training/check_sample_reviews.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DATA_DIR, MODELS_DIR  # noqa: E402
from nlp.preprocessing import TextPreprocessor  # noqa: E402

# id -> expected polarity for rows whose seed label is unambiguous
EXPECTED = {
    1: "positive", 2: "negative", 4: "neutral", 10: "positive", 11: "positive",
    12: "positive", 13: "negative", 14: "neutral", 15: "positive", 16: "negative",
    17: "positive", 18: "negative", 19: "neutral", 20: "negative",
    # 3 is mixed -> the 3-class model cannot emit "mixed"; informational only
}


def main() -> None:
    model = joblib.load(MODELS_DIR / "sentiment_model.pkl")
    vectorizer = joblib.load(MODELS_DIR / "sentiment_vectorizer.pkl")
    preprocessor = TextPreprocessor()

    with (DATA_DIR / "sample_reviews.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    correct = checked = 0
    print(f"{'id':>3}  {'pred':<9} conf    expected   review")
    for row in rows:
        text = row["review"].strip()
        pred = model.predict(vectorizer.transform([preprocessor.preprocess(text).model_text]))[0]
        proba = model.predict_proba(vectorizer.transform([preprocessor.preprocess(text).model_text]))[0]
        conf = max(proba)
        expected = EXPECTED.get(int(row["id"]), "")
        mark = ""
        if expected:
            checked += 1
            if pred == expected:
                correct += 1
                mark = " ok"
            else:
                mark = " MISS"
        print(f"{row['id']:>3}  {pred:<9} {conf:.2f}  {expected:<9} {text[:60]!r}{mark}")

    print(f"\nUnambiguous rows: {correct}/{checked} correct polarity")
    # probabilities sanity
    proba_all = model.predict_proba(
        vectorizer.transform([preprocessor.preprocess(r["review"]).model_text for r in rows])
    )
    dev = abs(proba_all.sum(axis=1) - 1.0).max()
    print(f"Probability rows sum to 1: max deviation {dev:.2e}")


if __name__ == "__main__":
    main()
