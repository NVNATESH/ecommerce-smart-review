"""Suspicious review detection (spec section 27).

These are heuristic signals - the product never claims a review is
provably fake; it reports "suspicious" with a score and reasons.
"""
from __future__ import annotations

import re

PROMO_PATTERNS = [
    r"\bbuy\s+now\b", r"\bdiscount\b", r"\bsale\b", r"\boffer\b", r"\bcoupon\b",
    r"\bfree\s+(shipping|gift|sample)\b", r"\blimited\s+(time|stock)\b",
    r"\bclick\s+here\b", r"\border\s+now\b", r"\b50%.*off\b", r"\bbest\s+price\b",
    r"https?://",
]
PROMO_RE = re.compile("|".join(PROMO_PATTERNS), re.IGNORECASE)

EXCESSIVE_PUNCT_RE = re.compile(r"[!?]{3,}")
ALL_CAPS_RE = re.compile(r"\b[A-Z]{5,}\b")


class SuspiciousReviewDetector:
    THRESHOLD = 50  # score >= 50 -> flagged suspicious

    def analyze(self, original_text: str, near_duplicate: bool, exact_duplicate: bool) -> dict:
        text = original_text.strip()
        reasons: list[str] = []
        score = 0

        words = text.split()
        upper_words = [w for w in words if w.isalpha() and w.isupper()]
        if words and len(upper_words) / max(len(words), 1) > 0.6 and len(text) > 12:
            score += 20
            reasons.append("shouted text (mostly capital letters)")

        if EXCESSIVE_PUNCT_RE.search(text):
            score += 20
            reasons.append("excessive punctuation")

        # repeated words: "BEST BEST BEST"
        lowered = [w.lower().strip(".,!?;:") for w in words]
        if lowered:
            max_repeat = max_repeated_run(lowered)
            if max_repeat >= 3:
                score += 25
                reasons.append("excessive repetition of the same words")
            elif max_repeat == 2 and len(lowered) <= 8:
                score += 10
                reasons.append("repeated words")

        # repeated characters inside words: "soooo goodddd" (originals only)
        if re.search(r"(.)\1{3,}", text):
            score += 10
            reasons.append("excessive repeated characters")

        if PROMO_RE.search(text):
            score += 25
            reasons.append("promotional language")

        alpha = sum(c.isalpha() for c in text)
        if 0 < len(text) <= 25 and alpha < 10 and not text.isdigit():
            score += 15
            reasons.append("extremely short low-content text")

        if exact_duplicate:
            score += 20
            reasons.append("exact duplicate of another review")
        if near_duplicate:
            score += 15
            reasons.append("near-duplicate of another review")

        score = min(100, score)
        return {
            "score": score,
            "suspicious": score >= self.THRESHOLD,
            "reasons": reasons,
        }


def max_repeated_run(tokens: list[str]) -> int:
    best = 1
    run = 1
    for i in range(1, len(tokens)):
        if tokens[i] and tokens[i] == tokens[i - 1]:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best
