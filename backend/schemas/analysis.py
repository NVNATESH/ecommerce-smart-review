"""Analysis-level response schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from schemas.review import ReviewResult, SentimentLabel


class AspectSummary(BaseModel):
    aspect: str
    mention_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    average_confidence: float
    overall: SentimentLabel


class ProsConsItem(BaseModel):
    aspect: str
    percentage: float
    mention_count: int
    average_confidence: float


class QualityComponentScores(BaseModel):
    review_detection: float
    opinion_density: float
    feature_density: float
    average_length: float
    language_quality: float
    dataset_diversity: float


class QualityReport(BaseModel):
    total_rows: int
    valid_reviews: int
    uncertain_reviews: int
    invalid_reviews: int
    exact_duplicates: int
    near_duplicates: int
    average_word_count: float
    opinion_density: float
    feature_density: float
    alphabetic_ratio: float
    gibberish_ratio: float
    excessive_symbol_ratio: float
    language_quality: float
    dataset_diversity: float
    quality_score: float
    dataset_decision: str
    reasons: list[str]
    component_scores: QualityComponentScores


class Verdict(BaseModel):
    """Factual product-level summary. Never an unconditional buy/don't-buy command."""

    overall_sentiment: str
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    statement: str
    strongest_positive_aspects: list[str]
    main_negative_aspects: list[str]


class AnalysisStatistics(BaseModel):
    reviews_analyzed: int
    duplicates_removed: int
    near_duplicates_detected: int
    invalid_reviews: int
    uncertain_reviews: int
    suspicious_reviews: int
    average_confidence: float
    average_word_count: float
    aspect_mentions_total: int
    processing_ms: int


class SentimentDistribution(BaseModel):
    positive: int
    neutral: int
    negative: int
    mixed: int
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    mixed_percentage: float


class ConfidenceHistogram(BaseModel):
    buckets: list[str]
    counts: list[int]


class AnalysisSummary(BaseModel):
    analysis_id: str
    created_at: str
    source: str  # "text" | "csv"
    filename: str | None = None
    detected_column: str | None = None
    status: str
    sentiment: SentimentDistribution
    confidence_histogram: ConfidenceHistogram
    quality: QualityReport
    aspects: list[AspectSummary]
    pros: list[ProsConsItem]
    cons: list[ProsConsItem]
    most_discussed: list[ProsConsItem]
    statistics: AnalysisStatistics
    verdict: Verdict


class AnalysisResponse(AnalysisSummary):
    reviews: list[ReviewResult]


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str  # "processing" | "completed" | "failed"
    progress: int  # 0-100
    stage: str
    error: dict[str, Any] | None = None
