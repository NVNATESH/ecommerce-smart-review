"""Real-data preparation pipeline.

Turns a raw labelled e-commerce review CSV into clean, stratified
train/validation/test splits with an auditable report.

Supported input formats
-----------------------
1. A user-supplied CSV with a review-text column named one of
   {review, text, review_text, comment, comments, feedback, customer_review,
   product_review} (case-insensitive) and a label column named one of
   {sentiment, label, rating, stars} (case-insensitive), where labels are
   either sentiment words (positive/negative/neutral, many safe variants
   accepted: "pos", "POSITIVE", "neg" ...) or numeric star ratings 1-5
   (1-2 -> negative, 3 -> neutral, 4-5 -> positive).

2. No --input: the real Amazon Reviews Multi (English) dataset
   (SetFit/amazon_reviews_multi_en, 200k product reviews, star labels 0-4)
   is downloaded from the Hugging Face hub and mapped the same way
   (0-1 -> negative, 2 -> neutral, 3-4 -> positive).

Cleaning performed (in order, all reported in prep_report.json):
    * drop null / empty / whitespace-only / duplicated-header rows
    * normalise labels safely (casefold + synonym map; unknown labels are
      dropped and counted, never silently remapped)
    * drop rows whose text length is < MIN_TEXT_CHARS
    * exact-duplicate removal on normalised text (casefold + whitespace
      collapse); conflicting duplicates (same text, different label) keep the
      first occurrence and are counted
    * optional stratified subsample (--max-rows) preserving class ratios
    * stratified 80/10/10 split (fixed seed) -> train/validation/test CSVs

Outputs (written to data/real/processed/):
    train.csv, validation.csv, test.csv  (columns: review, sentiment)
    prep_report.json                     (dataset provenance + cleaning audit)

Usage:
    python training/prepare_real_dataset.py                 # HF download
    python training/prepare_real_dataset.py --input my.csv  # user CSV
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import DATA_DIR  # noqa: E402

RAW_DIR = DATA_DIR / "real" / "raw"
PROCESSED_DIR = DATA_DIR / "real" / "processed"

SEED = 42
MIN_TEXT_CHARS = 3
TEXT_COLUMNS = ["review", "text", "review_text", "comment", "comments", "feedback", "customer_review", "product_review"]
LABEL_COLUMNS = ["sentiment", "label", "rating", "stars"]

# Safe label normalisation: everything maps INTO {positive, negative, neutral};
# anything unrecognised is dropped and counted, never guessed.
LABEL_MAP = {
    "positive": "positive", "pos": "positive", "p": "positive", "1": "positive",
    "negative": "negative", "neg": "negative", "n": "negative", "0": "negative",
    "neutral": "neutral", "neu": "neutral", "netural": "neutral", "2": "neutral",
    # star ratings
    "1star": "negative", "2star": "negative", "3star": "neutral", "4star": "positive", "5star": "positive",
    "one star": "negative", "two stars": "negative", "three stars": "neutral", "four stars": "positive", "five stars": "positive",
}
# HF amazon_reviews_multi labels are 0..4 == stars-1
STAR_LABEL_MAP = {0: "negative", 1: "negative", 2: "neutral", 3: "positive", 4: "positive"}
# user-supplied star ratings
RATING_MAP = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}


def normalise_label(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int,)) and not isinstance(value, bool):
        return RATING_MAP.get(value)
    if isinstance(value, float):
        if value.is_integer() and int(value) in RATING_MAP:
            return RATING_MAP[int(value)]
        return None
    s = str(value).strip().lower()
    if s.endswith(".0") and s[:-2].isdigit():
        return RATING_MAP.get(int(s[:-2]))
    if s in LABEL_MAP:
        return LABEL_MAP[s]
    # "4 stars", "3-star"
    for sep in (" ", "-", " "):
        if sep in s:
            head = s.split(sep)[0].strip()
            if head.isdigit() and int(head) in RATING_MAP:
                return RATING_MAP[int(head)]
    return None


def pick_column(columns: list[str], candidates: list[str]) -> str | None:
    lowered = {c.lower().strip(): c for c in columns}
    for cand in candidates:
        if cand in lowered:
            return lowered[cand]
    return None


def load_user_csv(path: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(path)
    text_col = pick_column(list(df.columns), TEXT_COLUMNS)
    label_col = pick_column(list(df.columns), LABEL_COLUMNS)
    if text_col is None or label_col is None:
        raise SystemExit(
            f"Could not identify text column ({TEXT_COLUMNS}) or label column "
            f"({LABEL_COLUMNS}) in {path.name}. Columns found: {list(df.columns)}"
        )
    out = pd.DataFrame({"review": df[text_col].astype(str), "sentiment": df[label_col]})
    return out, {"source_file": path.name, "text_column": text_col, "label_column": label_col}


def load_hf_dataset() -> tuple[pd.DataFrame, dict]:
    from datasets import load_dataset  # heavy import, only when needed

    ds = load_dataset("SetFit/amazon_reviews_multi_en", split="train")
    out = pd.DataFrame({
        "review": [str(t) for t in ds["text"]],
        "sentiment": [STAR_LABEL_MAP.get(int(l)) for l in ds["label"]],
    })
    return out, {
        "source_file": "huggingface:SetFit/amazon_reviews_multi_en[train]",
        "dataset_name": "Amazon Reviews Multi (English subset, McAuley-Lab)",
        "text_column": "text",
        "label_column": "label (0-4 == stars-1, mapped 0-1->negative, 2->neutral, 3-4->positive)",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=str, default=None, help="Path to a labelled CSV. Omit to download the Amazon Reviews Multi (EN) dataset.")
    parser.add_argument("--max-rows", type=int, default=None, help="Optional stratified subsample size after cleaning.")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1) load -----------------------------------------------------------------
    if args.input:
        raw, provenance = load_user_csv(Path(args.input))
    else:
        raw, provenance = load_hf_dataset()
    report: dict = {
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        **provenance,
        "rows_loaded": int(len(raw)),
    }

    # 2) drop null / empty ----------------------------------------------------
    raw["review"] = raw["review"].astype(str).str.strip()
    raw = raw[raw["review"] != ""]
    raw = raw[raw["review"].str.lower() != "nan"]
    raw = raw[raw["review"].str.lower() != "review"]  # duplicated header rows
    report["rows_after_null_empty_removal"] = int(len(raw))

    # 3) normalise labels safely ----------------------------------------------
    raw["sentiment"] = raw["sentiment"].map(normalise_label)
    unknown = raw["sentiment"].isna().sum()
    report["rows_with_unrecognised_label_dropped"] = int(unknown)
    raw = raw.dropna(subset=["sentiment"])

    # 4) minimum length ---------------------------------------------------------
    raw = raw[raw["review"].str.len() >= MIN_TEXT_CHARS]
    report["rows_after_min_length"] = int(len(raw))
    report["min_text_chars"] = MIN_TEXT_CHARS

    # 5) exact-duplicate removal ------------------------------------------------
    dedup_key = raw["review"].str.lower().str.replace(r"\s+", " ", regex=True)
    before = len(raw)
    raw = raw.assign(_key=dedup_key).drop_duplicates(subset="_key", keep="first").drop(columns="_key")
    report["exact_duplicates_removed"] = int(before - len(raw))

    # conflicting-label duplicates: same normalised text, different labels
    conflict_check = raw.assign(_key=raw["review"].str.lower().str.replace(r"\s+", " ", regex=True))
    conflicts = int((conflict_check.groupby("_key")["sentiment"].nunique() > 1).sum())
    report["conflicting_label_groups_kept_first"] = conflicts

    # 6) optional stratified subsample ------------------------------------------
    if args.max_rows and args.max_rows < len(raw):
        frac = args.max_rows / len(raw)
        raw, _ = train_test_split(
            raw, train_size=frac, stratify=raw["sentiment"], random_state=SEED,
        )
    report["rows_after_cleaning"] = int(len(raw))

    # 7) stratified 80/10/10 split ----------------------------------------------
    train_df, temp_df = train_test_split(
        raw, test_size=0.2, stratify=raw["sentiment"], random_state=SEED,
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.5, stratify=temp_df["sentiment"], random_state=SEED,
    )

    def dist(d: pd.DataFrame) -> dict[str, int]:
        return {k: int(v) for k, v in sorted(Counter(d["sentiment"]).items())}

    report.update({
        "train_samples": int(len(train_df)),
        "validation_samples": int(len(val_df)),
        "test_samples": int(len(test_df)),
        "class_distribution_overall": dist(raw),
        "class_distribution_train": dist(train_df),
        "class_distribution_validation": dist(val_df),
        "class_distribution_test": dist(test_df),
        "split": "80/10/10 stratified (sklearn train_test_split, seed=42)",
    })

    # 8) write -------------------------------------------------------------------
    for name, d in (("train", train_df), ("validation", val_df), ("test", test_df)):
        out = d[["review", "sentiment"]].reset_index(drop=True)
        out.to_csv(PROCESSED_DIR / f"{name}.csv", index=False, encoding="utf-8")
    (PROCESSED_DIR / "prep_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Loaded rows:        {report['rows_loaded']:,}")
    print(f"After cleaning:     {report['rows_after_cleaning']:,} "
          f"(dups removed: {report['exact_duplicates_removed']:,}, bad labels: {report['rows_with_unrecognised_label_dropped']:,})")
    print(f"Train: {report['train_samples']:,}  Validation: {report['validation_samples']:,}  Test: {report['test_samples']:,}")
    print(f"Overall class distribution: {report['class_distribution_overall']}")
    print(f"Wrote splits + prep_report.json -> {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
