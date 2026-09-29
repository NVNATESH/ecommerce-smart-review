"""Duplicate + near-duplicate detection.

Nothing is silently deleted: records are flagged and audit information is
kept so the frontend can show exactly what was marked and why.
"""
from __future__ import annotations

import hashlib
import logging

import numpy as np

from config import NEAR_DUPLICATE_SIMILARITY

logger = logging.getLogger("app.duplicates")


class DuplicateDetector:
    """Exact duplicates via normalized-text hash; near-duplicates via
    TF-IDF cosine similarity (sparse matrix product, no O(n^2) Python loop)."""

    def __init__(self, similarity_threshold: float = NEAR_DUPLICATE_SIMILARITY):
        self.similarity_threshold = similarity_threshold

    def detect(self, normalized_texts: list[str]) -> dict[int, dict]:
        """Returns {index: {"duplicate": bool, "near_duplicate": bool, "duplicate_of": int|None}}"""
        n = len(normalized_texts)
        flags: dict[int, dict] = {
            i: {"duplicate": False, "near_duplicate": False, "duplicate_of": None}
            for i in range(n)
        }
        if n < 2:
            return flags

        # --- exact duplicates -------------------------------------------------
        seen: dict[str, int] = {}
        for i, text in enumerate(normalized_texts):
            key = hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()
            if key in seen:
                flags[i]["duplicate"] = True
                flags[i]["duplicate_of"] = seen[key]
            else:
                seen[key] = i

        # --- near duplicates (skip exact duplicates) ---------------------------
        originals = [i for i, f in flags.items() if not f["duplicate"]]
        if len(originals) >= 2:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer

                texts = [normalized_texts[i] for i in originals]
                # Keep it bounded for very large datasets.
                if len(texts) <= 20000:
                    # char_wb 3-5 grams catch "battery life" vs "battery backup"
                    # style rewrites that word n-grams miss.
                    vec = TfidfVectorizer(
                        analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True,
                    )
                    X = vec.fit_transform(texts)
                    # cosine similarity == dot product of l2-normalised rows
                    sims = (X @ X.T).tocoo()
                    for i, j, s in zip(sims.row, sims.col, sims.data):
                        if i < j and s >= self.similarity_threshold:
                            a, b = originals[i], originals[j]
                            # keep the first occurrence, flag the later one
                            later = max(a, b)
                            earlier = min(a, b)
                            if not flags[later]["duplicate"] and not flags[later]["near_duplicate"]:
                                flags[later]["near_duplicate"] = True
                                flags[later]["duplicate_of"] = earlier
            except Exception as exc:  # near-dup is best-effort; exact dups still work
                logger.warning("Near-duplicate detection skipped: %s", exc)

        return flags

    @staticmethod
    def summarize(flags: dict[int, dict]) -> dict[str, int]:
        exact = sum(1 for f in flags.values() if f["duplicate"])
        near = sum(1 for f in flags.values() if f["near_duplicate"])
        return {"duplicates_removed": exact, "near_duplicates_detected": near}

    @staticmethod
    def kept_indices(flags: dict[int, dict]) -> list[int]:
        """Indices of records that are not exact duplicates (near-dups are kept
        but flagged - removal decisions are always explicit, never silent)."""
        return [i for i, f in flags.items() if not f["duplicate"]]
