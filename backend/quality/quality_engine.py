"""Data Quality Engine (spec section 28).

Combines transparent component scores into a single quality_score (0-100)
and a dataset_decision (ACCEPT / ACCEPT WITH WARNING / REJECT) with reasons.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from config import QUALITY_ACCEPT, QUALITY_ACCEPT_WITH_WARNING

# Weights are documented so the score stays explainable and auditable.
WEIGHTS = {
    "review_detection": 0.25,
    "opinion_density": 0.15,
    "feature_density": 0.10,
    "average_length": 0.15,
    "language_quality": 0.20,
    "dataset_diversity": 0.15,
}


def average_length_score(avg_word_count: float) -> float:
    if avg_word_count >= 5:
        return 100.0
    if avg_word_count >= 3:
        return 60.0
    if avg_word_count >= 2:
        return 30.0
    return 10.0


@dataclass
class QualityAssessment:
    quality_score: float
    dataset_decision: str
    reasons: list[str] = field(default_factory=list)
    component_scores: dict[str, float] = field(default_factory=dict)
    duplicate_penalty: float = 0.0
    uncertainty_penalty: float = 0.0


def compute_quality(
    *,
    valid_ratio: float,          # fraction VALID per review detector
    uncertain_ratio: float,      # fraction UNCERTAIN
    duplicate_ratio: float,      # fraction exact duplicates
    near_duplicate_ratio: float, # fraction near-duplicates
    opinion_density: float,
    feature_density: float,
    average_word_count: float,
    language_quality: float,
    dataset_diversity: float,
    review_count_decision: str,
) -> QualityAssessment:
    components = {
        "review_detection": round(valid_ratio * 100 + 0.5 * uncertain_ratio * 100, 1),
        "opinion_density": round(min(1.0, opinion_density / 0.8) * 100, 1),
        "feature_density": round(min(1.0, feature_density / 0.5) * 100, 1),
        "average_length": average_length_score(average_word_count),
        "language_quality": round(language_quality, 1),
        "dataset_diversity": round(min(1.0, dataset_diversity / 0.6) * 100, 1),
    }

    base = sum(components[k] * w for k, w in WEIGHTS.items())
    duplicate_penalty = round((duplicate_ratio + near_duplicate_ratio) * 30, 1)
    uncertainty_penalty = round(uncertain_ratio * 20, 1)
    score = max(0.0, min(100.0, base - duplicate_penalty - uncertainty_penalty))

    reasons: list[str] = []
    if components["review_detection"] < 70:
        reasons.append(
            f"Only {round(valid_ratio * 100)}% of rows were classified as valid reviews."
        )
    if components["opinion_density"] < 40:
        reasons.append(
            f"Opinion density is low ({round(opinion_density * 100)}% of reviews contain opinion words)."
        )
    if components["language_quality"] < 50:
        reasons.append(
            f"Language quality is low (alphabetic ratio, gibberish and symbol-heavy rows scored {round(language_quality)}/100)."
        )
    if duplicate_ratio > 0.1:
        reasons.append(f"{round(duplicate_ratio * 100)}% of reviews are exact duplicates.")
    if near_duplicate_ratio > 0.1:
        reasons.append(f"{round(near_duplicate_ratio * 100)}% of reviews are near-duplicates.")
    if components["dataset_diversity"] < 40:
        reasons.append("Vocabulary diversity is low; reviews repeat the same phrasing.")
    if review_count_decision == "WARNING":
        reasons.append("Review count is below the recommended minimum of 5.")
    if not reasons:
        reasons.append("Dataset passed all quality checks.")

    if score >= QUALITY_ACCEPT:
        decision = "ACCEPT"
    elif score >= QUALITY_ACCEPT_WITH_WARNING:
        decision = "ACCEPT WITH WARNING"
    else:
        decision = "REJECT"

    return QualityAssessment(
        quality_score=round(score, 1),
        dataset_decision=decision,
        reasons=reasons,
        component_scores=components,
        duplicate_penalty=duplicate_penalty,
        uncertainty_penalty=uncertainty_penalty,
    )
