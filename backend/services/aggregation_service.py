"""Aggregation engine: dataset-level sentiment, pros/cons, verdict, statistics.

All thresholds are explicit so the product-level verdict stays transparent.
The verdict is factual - it never issues an unconditional Buy / Don't Buy.
"""
from __future__ import annotations

from schemas.analysis import (
    AnalysisStatistics,
    ConfidenceHistogram,
    ProsConsItem,
    SentimentDistribution,
    Verdict,
)
from schemas.review import ReviewResult
from config import MIN_MENTIONS_FOR_PRO_CON, PRO_CON_LIST_CAP

MIN_MENTIONS = MIN_MENTIONS_FOR_PRO_CON


def build_distribution(reviews: list[ReviewResult]) -> SentimentDistribution:
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0, "Mixed": 0}
    for r in reviews:
        counts[r.sentiment.value] += 1
    n = max(len(reviews), 1)

    def pct(c: int) -> float:
        return round(c / n * 100, 1)

    return SentimentDistribution(
        positive=counts["Positive"],
        neutral=counts["Neutral"],
        negative=counts["Negative"],
        mixed=counts["Mixed"],
        positive_percentage=pct(counts["Positive"]),
        neutral_percentage=pct(counts["Neutral"]),
        negative_percentage=pct(counts["Negative"]),
        mixed_percentage=pct(counts["Mixed"]),
    )


def build_confidence_histogram(reviews: list[ReviewResult]) -> ConfidenceHistogram:
    buckets = ["0-50%", "50-70%", "70-85%", "85-95%", "95-100%"]
    counts = [0] * len(buckets)
    for r in reviews:
        c = r.confidence
        if c < 0.5:
            counts[0] += 1
        elif c < 0.7:
            counts[1] += 1
        elif c < 0.85:
            counts[2] += 1
        elif c < 0.95:
            counts[3] += 1
        else:
            counts[4] += 1
    return ConfidenceHistogram(buckets=buckets, counts=counts)


def _pick(aspects: list, polarity: str) -> list[ProsConsItem]:
    """All aspects that lean toward `polarity`, strongest first.

    Rules (transparent, spec sections 24/25):
      * Pros: positive mentions outnumber negative ones; Cons: the reverse.
        Balanced aspects (equal for/against) appear in neither list.
      * Ranked by leaning percentage, then by mention volume weighted by
        confidence, so aspects discussed many times always rank above
        single-review ones - a single review never creates a *major*
        pro or con.
      * Capped at PRO_CON_LIST_CAP entries; mention counts stay visible in
        the UI so the evidence weight of each entry is honest.
    """
    if polarity == "positive":
        eligible = [a for a in aspects if a.positive_count > a.negative_count]
        key = "positive_percentage"
    else:
        eligible = [a for a in aspects if a.negative_count > a.positive_count]
        key = "negative_percentage"
    eligible.sort(
        key=lambda a: (getattr(a, key), a.mention_count * (0.5 + a.average_confidence)),
        reverse=True,
    )
    return [
        ProsConsItem(
            aspect=a.aspect,
            percentage=getattr(a, key),
            mention_count=a.mention_count,
            average_confidence=a.average_confidence,
        )
        for a in eligible[:PRO_CON_LIST_CAP]
    ]


def _evidence_quotes(aspect_name: str, sentiment_label: str, reviews: list) -> list[str]:
    """Up to 2 real review quotes supporting one pro/con aspect — strongest
    confidence first, VALID preferred, so every claim shows its evidence."""
    matches = [
        r for r in reviews
        if any(m.category == aspect_name and m.sentiment.value == sentiment_label for m in r.aspects)
    ]
    matches.sort(key=lambda r: (r.review_status.value == "VALID", r.confidence), reverse=True)
    out = []
    for r in matches[:2]:
        q = r.original_text if len(r.original_text) <= 140 else r.original_text[:137] + "..."
        entry = f"\u201c{q}\u201d \u2014 review #{r.id}"
        if entry not in out:
            out.append(entry)
    return out


def build_pros_cons(aspects: list, reviews: list | None = None) -> tuple[list[ProsConsItem], list[ProsConsItem]]:
    """Every aspect that leans positive becomes a pro entry, every aspect
    that leans negative a con entry (ranked strongest first). Balanced
    aspects appear in neither list. Each entry carries up to 2 real review
    quotes as evidence."""
    pos_items, neg_items = _pick(aspects, "positive"), _pick(aspects, "negative")
    if reviews:
        for item in pos_items:
            item.quotes = _evidence_quotes(item.aspect, "Positive", reviews)
        for item in neg_items:
            item.quotes = _evidence_quotes(item.aspect, "Negative", reviews)
    return pos_items, neg_items


def build_verdict(reviews: list[ReviewResult], aspects: list, quality_score: float) -> Verdict:
    dist = build_distribution(reviews)
    pos, neg = dist.positive_percentage, dist.negative_percentage

    # Transparent aggregation rules for the overall label (spec section 63).
    if dist.mixed_percentage >= 25 or (pos >= 30 and neg >= 30):
        label = "Mixed"
    elif pos >= 80:
        label = "Strongly Positive"
    elif pos >= 55:
        label = "Predominantly Positive"
    elif neg >= 80:
        label = "Strongly Negative"
    elif neg >= 55:
        label = "Predominantly Negative"
    elif dist.neutral_percentage >= 60:
        label = "Neutral"
    elif pos > neg:
        label = "Predominantly Positive"
    else:
        label = "Predominantly Negative"

    pros = _pick(aspects, "positive")[:3]
    cons = _pick(aspects, "negative")[:3]

    statement = (
        f"Customer sentiment is {label.lower()}: {dist.positive_percentage}% positive, "
        f"{dist.neutral_percentage}% neutral and {dist.negative_percentage}% negative "
        f"across {len(reviews)} analysed reviews (dataset quality {round(quality_score)}/100)."
    )
    if pros:
        statement += f" Customers most favour: {', '.join(p.aspect for p in pros)}."
    if cons:
        statement += f" Main complaints concern: {', '.join(c.aspect for c in cons)}."

    return Verdict(
        overall_sentiment=label,
        positive_percentage=dist.positive_percentage,
        neutral_percentage=dist.neutral_percentage,
        negative_percentage=dist.negative_percentage,
        statement=statement,
        strongest_positive_aspects=[p.aspect for p in pros],
        main_negative_aspects=[c.aspect for c in cons],
    )


def build_statistics(
    reviews: list[ReviewResult],
    *,
    exact_duplicates: int,
    near_duplicates: int,
    processing_ms: int,
    aspect_mention_total: int,
) -> AnalysisStatistics:
    n = max(len(reviews), 1)
    return AnalysisStatistics(
        reviews_analyzed=len(reviews),
        duplicates_removed=exact_duplicates,
        near_duplicates_detected=near_duplicates,
        invalid_reviews=sum(1 for r in reviews if r.review_status.value == "INVALID"),
        uncertain_reviews=sum(1 for r in reviews if r.review_status.value == "UNCERTAIN"),
        suspicious_reviews=sum(1 for r in reviews if r.suspicious),
        average_confidence=round(sum(r.confidence for r in reviews) / n, 4),
        average_word_count=round(sum(r.word_count for r in reviews) / n, 2),
        aspect_mentions_total=aspect_mention_total,
        processing_ms=processing_ms,
    )
