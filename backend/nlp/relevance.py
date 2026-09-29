"""Product relevance (spec section 16).

Computed independently from the review detector. A review is NOT rejected
merely because it contains unrelated words - relevance is a graded signal
combining aspect presence, opinion indicators, detector probability and
contextual product-domain evidence.
"""
from __future__ import annotations

import re

from nlp.aspect_engine import NEG_WORDS, POS_WORDS, detect_aspects

PRODUCT_CONTEXT_RE = re.compile(
    r"\b(product|phone|smartphone|mobile|laptop|tablet|earbuds|earphones|headphones|"
    r"speaker|watch|camera|television|tv|device|item|purchase|purchased|bought|buy|"
    r"ordered|order|delivered|delivery|price|money|warranty|brand|quality|package|"
    r"packaging|using|used|month|months|year|years|week|weeks|days?)\b",
    re.IGNORECASE,
)


def relevance_score(
    original_text: str,
    *,
    aspect_count: int,
    review_probability: float,
) -> float:
    lower = original_text.lower()
    tokens = re.findall(r"[a-z']+", lower)

    aspect_signal = min(aspect_count, 3) / 3 if aspect_count else 0.0
    opinion_signal = 1.0 if any(t in POS_WORDS or t in NEG_WORDS for t in tokens) else 0.0
    context_signal = 1.0 if PRODUCT_CONTEXT_RE.search(original_text) else 0.0
    detector_signal = review_probability

    score = (
        0.40 * aspect_signal
        + 0.30 * opinion_signal
        + 0.15 * context_signal
        + 0.15 * detector_signal
    )
    return round(min(1.0, score), 3)


def relevance_level(score: float) -> str:
    if score >= 0.7:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"
