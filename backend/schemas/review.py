"""Per-review result schemas (mirrored in frontend/lib/types.ts)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class SentimentLabel(str, Enum):
    positive = "Positive"
    negative = "Negative"
    neutral = "Neutral"
    mixed = "Mixed"


class ReviewStatus(str, Enum):
    valid = "VALID"
    uncertain = "UNCERTAIN"
    invalid = "INVALID"


class RelevanceLevel(str, Enum):
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"


class AspectMention(BaseModel):
    category: str
    sentiment: SentimentLabel
    confidence: float


class ReviewResult(BaseModel):
    id: int
    original_text: str
    normalized_text: str
    word_count: int
    review_probability: float
    not_review_probability: float
    review_status: ReviewStatus
    relevance: float
    relevance_level: RelevanceLevel
    sentiment: SentimentLabel
    confidence: float
    positive_probability: float
    negative_probability: float
    neutral_probability: float
    aspects: list[AspectMention]
    suspicion_score: int
    suspicious: bool
    suspicion_reasons: list[str]
    contributing_terms: list[str]
    duplicate: bool = False
    near_duplicate: bool = False
    duplicate_of: int | None = None


class ReviewPage(BaseModel):
    analysis_id: str
    page: int
    page_size: int
    total: int
    total_pages: int
    reviews: list[ReviewResult]
