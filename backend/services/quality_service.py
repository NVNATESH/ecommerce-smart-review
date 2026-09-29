"""Quality service: combines dataset metrics + review detection into the report."""
from __future__ import annotations

from quality.quality_engine import compute_quality
from schemas.analysis import QualityComponentScores, QualityReport
from validation.review_validator import DatasetMetrics


def build_quality_report(
    *,
    metrics: DatasetMetrics,
    total_rows: int,
    exact_duplicates: int,
    near_duplicates: int,
    valid_reviews: int,
    uncertain_reviews: int,
    invalid_reviews: int,
) -> QualityReport:
    n = max(total_rows, 1)
    assessment = compute_quality(
        valid_ratio=valid_reviews / n,
        uncertain_ratio=uncertain_reviews / n,
        duplicate_ratio=exact_duplicates / n,
        near_duplicate_ratio=near_duplicates / n,
        opinion_density=metrics.opinion_density,
        feature_density=metrics.feature_density,
        average_word_count=metrics.average_word_count,
        language_quality=metrics.language_quality,
        dataset_diversity=metrics.dataset_diversity,
        review_count_decision=metrics.review_count_decision,
    )

    if metrics.review_count_decision == "REJECT":
        decision = "REJECT"
        reasons = list(metrics.reasons) + [
            "Dataset rejected: too few reviews to produce reliable intelligence."
        ]
    else:
        decision = assessment.dataset_decision
        reasons = metrics.reasons + assessment.reasons if decision != "ACCEPT" else list(assessment.reasons)

    return QualityReport(
        total_rows=total_rows,
        valid_reviews=valid_reviews,
        uncertain_reviews=uncertain_reviews,
        invalid_reviews=invalid_reviews,
        exact_duplicates=exact_duplicates,
        near_duplicates=near_duplicates,
        average_word_count=metrics.average_word_count,
        opinion_density=metrics.opinion_density,
        feature_density=metrics.feature_density,
        alphabetic_ratio=metrics.alphabetic_ratio,
        gibberish_ratio=metrics.gibberish_ratio,
        excessive_symbol_ratio=metrics.excessive_symbol_ratio,
        language_quality=metrics.language_quality,
        dataset_diversity=metrics.dataset_diversity,
        quality_score=assessment.quality_score,
        dataset_decision=decision,
        reasons=list(dict.fromkeys(reasons)),
        component_scores=QualityComponentScores(**assessment.component_scores),
    )
