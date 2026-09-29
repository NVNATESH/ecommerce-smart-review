"""Dataset-level review validation (spec section 14).

Computes review count, average length, opinion density, feature density,
alphabetic ratio, gibberish ratio and excessive symbol ratio, and maps them
to the dataset decision rules.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from config import (
    AVG_WORD_COUNT_GOOD,
    AVG_WORD_COUNT_WARNING,
    DATASET_REVIEW_COUNT_VALID,
    DATASET_REVIEW_COUNT_WARNING,
)
from nlp.aspect_engine import NEG_WORDS, POS_WORDS, detect_aspects
from nlp.keyword_extractor import vocabulary_richness
from nlp.text_utils import ALPHA_RE, SYMBOL_RE

JUNK_TOKEN_RE = re.compile(r"^[^aeiouy]{4,}$", re.IGNORECASE)


@dataclass
class DatasetMetrics:
    review_count: int = 0
    average_word_count: float = 0.0
    opinion_density: float = 0.0
    feature_density: float = 0.0
    alphabetic_ratio: float = 0.0
    gibberish_ratio: float = 0.0
    excessive_symbol_ratio: float = 0.0
    language_quality: float = 0.0
    dataset_diversity: float = 0.0
    reasons: list[str] = field(default_factory=list)
    review_count_decision: str = "REJECT"
    average_length_decision: str = "REJECT"


def gibberish_score(text: str) -> float:
    """Heuristic 0-1 score: share of tokens that look like keyboard noise.

    Symbol-heavy strings with little alphabetic content ("asd123###") count
    as fully junky.
    """
    tokens = re.findall(r"[A-Za-z]+", text)
    non_space = [c for c in text if not c.isspace()]
    if not non_space:
        return 1.0
    alpha_ratio = sum(c.isalpha() for c in non_space) / len(non_space)
    if alpha_ratio < 0.5:
        return 1.0
    if not tokens:
        return 1.0
    junk = sum(
        1 for t in tokens
        if len(t) >= 3 and (
            JUNK_TOKEN_RE.match(t)
            or re.search(r"(.)\1\1", t)  # aaa inside token (uncollapsed originals)
            or (sum(c in "aeiouy" for c in t.lower()) == 0)
        )
    )
    return junk / len(tokens)


def language_quality_score(
    alphabetic_ratio: float,
    gibberish_ratio: float,
    excessive_symbol_ratio: float,
) -> float:
    score = 100.0
    score -= max(0.0, 1 - alphabetic_ratio) * 60
    score -= gibberish_ratio * 60
    score -= excessive_symbol_ratio * 40
    return round(max(0.0, min(100.0, score)), 1)


def compute_dataset_metrics(
    original_texts: list[str],
    word_counts: list[int],
    alphabetic_ratios: list[float],
    symbol_ratios: list[float],
) -> DatasetMetrics:
    m = DatasetMetrics(review_count=len(original_texts))
    if not original_texts:
        return m

    m.average_word_count = round(sum(word_counts) / len(word_counts), 2)
    m.opinion_density = round(
        sum(1 for t in original_texts if any(w in POS_WORDS or w in NEG_WORDS for w in re.findall(r"[a-z']+", t.lower())))
        / len(original_texts), 3,
    )
    m.feature_density = round(
        sum(1 for t in original_texts if detect_aspects(t)) / len(original_texts), 3,
    )
    m.alphabetic_ratio = round(sum(alphabetic_ratios) / len(alphabetic_ratios), 3)
    gib = [gibberish_score(t) for t in original_texts]
    m.gibberish_ratio = round(sum(1 for g in gib if g > 0.5) / len(gib), 3)
    m.excessive_symbol_ratio = round(sum(1 for s in symbol_ratios if s > 0.3) / len(symbol_ratios), 3)
    m.dataset_diversity = round(vocabulary_richness(original_texts), 3)
    m.language_quality = language_quality_score(
        m.alphabetic_ratio, m.gibberish_ratio, m.excessive_symbol_ratio,
    )

    # Decision rules ---------------------------------------------------------
    if m.review_count >= DATASET_REVIEW_COUNT_VALID:
        m.review_count_decision = "VALID"
    elif m.review_count >= DATASET_REVIEW_COUNT_WARNING:
        m.review_count_decision = "WARNING"
        m.reasons.append(
            f"Only {m.review_count} reviews provided; at least "
            f"{DATASET_REVIEW_COUNT_VALID} are recommended for reliable results."
        )
    else:
        m.review_count_decision = "REJECT"
        m.reasons.append(
            f"Only {m.review_count} reviews provided; at least "
            f"{DATASET_REVIEW_COUNT_WARNING} are required."
        )

    if m.average_word_count >= AVG_WORD_COUNT_GOOD:
        m.average_length_decision = "GOOD"
    elif m.average_word_count >= AVG_WORD_COUNT_WARNING:
        m.average_length_decision = "WARNING"
        m.reasons.append(
            f"Average review length is {m.average_word_count} words; reviews of "
            f"{AVG_WORD_COUNT_GOOD}+ words give more reliable sentiment signals."
        )
    else:
        m.average_length_decision = "REJECT"
        m.reasons.append(
            f"Average review length is only {m.average_word_count} words."
        )

    if m.gibberish_ratio > 0.3:
        m.reasons.append(f"{round(m.gibberish_ratio * 100)}% of reviews look like gibberish.")
    if m.excessive_symbol_ratio > 0.3:
        m.reasons.append(f"{round(m.excessive_symbol_ratio * 100)}% of reviews are symbol-heavy.")
    return m
