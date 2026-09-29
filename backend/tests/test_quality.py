"""Quality engine tests (spec section 28 rules)."""
from __future__ import annotations

from quality.quality_engine import compute_quality
from validation.review_validator import compute_dataset_metrics, gibberish_score


def base_kwargs(**overrides):
    kwargs = dict(
        valid_ratio=0.95,
        uncertain_ratio=0.03,
        duplicate_ratio=0.01,
        near_duplicate_ratio=0.01,
        opinion_density=0.85,
        feature_density=0.55,
        average_word_count=9.0,
        language_quality=92.0,
        dataset_diversity=0.55,
        review_count_decision="VALID",
    )
    kwargs.update(overrides)
    return kwargs


class TestQualityEngine:
    def test_high_quality_accepts(self):
        result = compute_quality(**base_kwargs())
        assert result.dataset_decision == "ACCEPT"
        assert result.quality_score >= 80

    def test_reject_on_poor_inputs(self):
        result = compute_quality(**base_kwargs(
            valid_ratio=0.2, uncertain_ratio=0.2, opinion_density=0.1,
            feature_density=0.05, average_word_count=2.0, language_quality=30.0,
            dataset_diversity=0.15,
        ))
        assert result.dataset_decision == "REJECT"
        assert result.quality_score < 60

    def test_warning_band(self):
        result = compute_quality(**base_kwargs(
            valid_ratio=0.6, uncertain_ratio=0.15, opinion_density=0.4,
            duplicate_ratio=0.1,
        ))
        assert result.dataset_decision == "ACCEPT WITH WARNING"
        assert 60 <= result.quality_score < 80

    def test_duplicate_penalty_applied(self):
        clean = compute_quality(**base_kwargs())
        duped = compute_quality(**base_kwargs(duplicate_ratio=0.2))
        assert duped.quality_score < clean.quality_score

    def test_reasons_always_present(self):
        result = compute_quality(**base_kwargs())
        assert result.reasons


class TestDatasetMetrics:
    def test_minimum_reviews_reject(self):
        metrics = compute_dataset_metrics(
            ["Great battery."],
            [2],
            [0.9],
            [0.05],
        )
        assert metrics.review_count_decision == "REJECT"

    def test_warning_band(self):
        metrics = compute_dataset_metrics(
            ["Great battery and the screen is bright.", "Camera is terrible.", "It has 128GB storage."],
            [8, 3, 6],
            [0.95, 0.9, 0.92],
            [0.02, 0.03, 0.02],
        )
        assert metrics.review_count_decision == "WARNING"

    def test_gibberish_detected(self):
        assert gibberish_score("asd123###") > 0.5
        assert gibberish_score("The battery is excellent and lasts long.") < 0.2
