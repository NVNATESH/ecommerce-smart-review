"""Analysis pipeline orchestrator.

Route -> Service -> NLP/ML engines -> Response schema. This module runs the
full pipeline for pasted text and CSV jobs and persists results in the
AnalysisStore (in-memory for v1, structured so a database can replace it).
"""
from __future__ import annotations

import logging
import math
import time
import uuid
from datetime import datetime, timezone

from api.errors import ModelNotLoadedError
from ml.explainability import explain_prediction
from ml.model_manager import ModelManager
from nlp.emotions import detect_emotions
from nlp.relevance import relevance_level, relevance_score
from schemas.review import AspectMention, ReviewResult
from services.aggregation_service import (
    build_confidence_histogram,
    build_distribution,
    build_pros_cons,
    build_statistics,
    build_verdict,
)
from services.aspect_service import AspectService
from services.duplicate_service import DuplicateDetector
from services.preprocessing_service import PreprocessingService
from services.quality_service import build_quality_report
from services.review_detector_service import ReviewDetectorService
from services.sentiment_service import SentimentService
from services.suspicious_review_service import SuspiciousReviewDetector
from validation.input_validator import validate_review_texts
from validation.review_validator import compute_dataset_metrics

logger = logging.getLogger("app.analysis")


class AnalysisStore:
    """In-memory analysis result store. Keyed by opaque analysis_id.

    Designed behind a small interface so a database (e.g. PostgreSQL) can be
    swapped in later without touching the NLP engine.
    """

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}
        self._reviews: dict[str, list[ReviewResult]] = {}

    def create(self, source: str, filename: str | None = None, detected_column: str | None = None) -> str:
        analysis_id = uuid.uuid4().hex[:16]
        self._data[analysis_id] = {
            "analysis_id": analysis_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "filename": filename,
            "detected_column": detected_column,
            "status": "processing",
            "progress": 0,
            "stage": "Queued",
            "error": None,
        }
        return analysis_id

    def set_progress(self, analysis_id: str, progress: int, stage: str) -> None:
        record = self._data.get(analysis_id)
        if record:
            record["progress"] = int(progress)
            record["stage"] = stage

    def set_completed(self, analysis_id: str, summary: dict) -> None:
        record = self._data.get(analysis_id)
        if record:
            record.update(summary)
            record["status"] = "completed"
            record["progress"] = 100
            record["stage"] = "Completed"

    def set_failed(self, analysis_id: str, code: str, message: str) -> None:
        record = self._data.get(analysis_id)
        if record:
            record["status"] = "failed"
            record["error"] = {"code": code, "message": message}

    def get(self, analysis_id: str) -> dict | None:
        return self._data.get(analysis_id)

    def get_reviews(self, analysis_id: str) -> list[ReviewResult] | None:
        return self._reviews.get(analysis_id)

    def put_reviews(self, analysis_id: str, reviews: list[ReviewResult]) -> None:
        self._reviews[analysis_id] = reviews

    def ingest(self, analysis_id: str, summary: dict, review_models: list[ReviewResult]) -> None:
        """Register a completed analysis under a (possibly new) analysis_id —
        used to pin product analyses under their stable product id."""
        self._data[analysis_id] = {
            **summary,
            "analysis_id": analysis_id,
            "status": "completed",
            "progress": 100,
            "stage": "Completed",
        }
        self._reviews[analysis_id] = review_models

    def remove(self, analysis_id: str) -> None:
        self._data.pop(analysis_id, None)
        self._reviews.pop(analysis_id, None)


class AnalysisPipeline:
    STAGES = [
        (5, "Validating..."),
        (12, "Detecting reviews..."),
        (25, "Removing duplicates..."),
        (40, "Preprocessing..."),
        (55, "Running sentiment model..."),
        (70, "Extracting aspects..."),
        (80, "Calculating quality..."),
        (90, "Generating dashboard..."),
    ]

    def __init__(self, manager: ModelManager):
        if not manager.loaded:
            raise ModelNotLoadedError(
                "MODELS_NOT_LOADED",
                "ML models are not loaded. Run the training scripts and restart the server.",
            )
        self.manager = manager
        self.preprocessing = PreprocessingService()
        self.review_detector = ReviewDetectorService(manager)
        self.sentiment = SentimentService(manager)
        self.aspect_service = AspectService()
        self.duplicates = DuplicateDetector()
        self.suspicious = SuspiciousReviewDetector()
        # TF-IDF feature names are fixed once the vectorizer is loaded; building
        # them costs ~0.65 s, so compute them once here instead of per analysis.
        self.feature_names = manager.sentiment_vectorizer.get_feature_names_out()

    def run(
        self,
        analysis_id: str,
        raw_reviews: list[str],
        source: str,
        store: AnalysisStore,
        *,
        filename: str | None = None,
        detected_column: str | None = None,
        progress_cb=None,
    ) -> dict:
        started = time.perf_counter()

        def stage(pct: int, name: str) -> None:
            store.set_progress(analysis_id, pct, name)
            if progress_cb:
                progress_cb(pct, name)

        # 1) validation -------------------------------------------------------
        length_check = validate_review_texts(raw_reviews)
        if not length_check.valid:
            raise ValueError(length_check.message)

        stage(12, "Detecting reviews...")
        detector_results = self.review_detector.score(raw_reviews)

        stage(25, "Removing duplicates...")
        preprocessed = self.preprocessing.preprocess_batch(raw_reviews)
        dup_flags = self.duplicates.detect([p.normalized_text for p in preprocessed])
        dup_summary = DuplicateDetector.summarize(dup_flags)

        stage(40, "Preprocessing...")
        # (batch preprocessing already done above; kept as an explicit stage
        #  because it is the second-most expensive step for large CSVs)

        stage(55, "Running sentiment model...")
        aspect_mentions: list[list] = []
        clause_analyses_per_review: list[list] = []
        for p in preprocessed:
            mentions, clauses = self.aspect_service.analyze_review(p.original_text)
            aspect_mentions.append(mentions)
            clause_analyses_per_review.append(clauses)
        sentiment_results = self.sentiment.score(
            [p.model_text for p in preprocessed], clause_analyses_per_review,
            emoji_signals=[{"pos": p.emoji_pos, "neg": p.emoji_neg} for p in preprocessed],
        )

        stage(70, "Extracting aspects...")
        vectorizer = self.manager.sentiment_vectorizer
        model = self.manager.sentiment_model
        classes = self.sentiment.engine.classes
        feature_names = self.feature_names  # cached at pipeline construction

        reviews: list[ReviewResult] = []
        for i, p in enumerate(preprocessed):
            d, s, m = detector_results[i], sentiment_results[i], aspect_mentions[i]
            rel = relevance_score(
                p.original_text,
                aspect_count=len(m),
                review_probability=d["review_probability"],
            )
            contributing = explain_prediction(
                p.model_text, vectorizer, model,
                class_label=s["sentiment"] if s["sentiment"] in classes else classes[0],
                classes=classes,
                feature_names=feature_names,
            ) if p.model_text else []
            susp = self.suspicious.analyze(
                p.original_text,
                near_duplicate=dup_flags[i]["near_duplicate"],
                exact_duplicate=dup_flags[i]["duplicate"],
            )
            reviews.append(ReviewResult(
                id=i + 1,
                original_text=p.original_text,
                normalized_text=p.normalized_text,
                word_count=p.word_count,
                review_probability=d["review_probability"],
                not_review_probability=d["not_review_probability"],
                review_status=d["review_status"],
                relevance=rel,
                relevance_level=relevance_level(rel),
                sentiment=s["sentiment"],
                confidence=s["confidence"],
                positive_probability=s["positive_probability"],
                negative_probability=s["negative_probability"],
                neutral_probability=s["neutral_probability"],
                aspects=[AspectMention(**a.__dict__) for a in m],
                suspicion_score=susp["score"],
                suspicious=susp["suspicious"],
                suspicion_reasons=susp["reasons"],
                contributing_terms=contributing,
                duplicate=dup_flags[i]["duplicate"],
                near_duplicate=dup_flags[i]["near_duplicate"],
                duplicate_of=dup_flags[i]["duplicate_of"] + 1 if dup_flags[i]["duplicate_of"] is not None else None,
            ))

        stage(80, "Calculating quality...")
        metrics = compute_dataset_metrics(
            [p.original_text for p in preprocessed],
            [p.word_count for p in preprocessed],
            [p.alphabetic_ratio for p in preprocessed],
            [p.symbol_ratio for p in preprocessed],
        )
        valid_n = sum(1 for r in reviews if r.review_status.value == "VALID")
        uncertain_n = sum(1 for r in reviews if r.review_status.value == "UNCERTAIN")
        invalid_n = sum(1 for r in reviews if r.review_status.value == "INVALID")
        quality = build_quality_report(
            metrics=metrics,
            total_rows=len(reviews),
            exact_duplicates=dup_summary["duplicates_removed"],
            near_duplicates=dup_summary["near_duplicates_detected"],
            valid_reviews=valid_n,
            uncertain_reviews=uncertain_n,
            invalid_reviews=invalid_n,
        )

        # Trust score — how much this dataset's verdict can be trusted
        # (transparent weighted mix; components returned for the UI)
        n_total = max(len(reviews), 1)
        valid_pct = valid_n / n_total * 100
        susp_pct = sum(1 for r in reviews if r.suspicious) / n_total * 100
        dup_pct = (dup_summary["duplicates_removed"] + dup_summary["near_duplicates_detected"]) / n_total * 100
        volume_score = min(100.0, 10.0 * math.sqrt(len(reviews)))
        trust_score = round(
            0.35 * valid_pct + 0.25 * (100 - susp_pct) + 0.20 * (100 - dup_pct)
            + 0.20 * min(100.0, volume_score), 1)
        trust_band = ("High confidence" if trust_score >= 80
                      else "Moderate confidence" if trust_score >= 60 else "Low confidence")
        trust = {
            "score": trust_score,
            "band": trust_band,
            "components": {
                "validReviewPct": round(valid_pct, 1),
                "suspiciousPct": round(susp_pct, 1),
                "duplicatePct": round(dup_pct, 1),
                "volumeScore": round(min(100.0, volume_score), 1),
                "qualityScore": quality.quality_score,
            },
        }

        # Emotion mix (lexicon-based, dataset level)
        emotion_counts = {e: 0 for e in ("Joy", "Love", "Anger", "Sadness", "Fear")}
        no_emotion = 0
        for r in reviews:
            emos = detect_emotions(r.original_text)
            hit = False
            for e, present in emos.items():
                if present:
                    emotion_counts[e] += 1
                    hit = True
            if not hit:
                no_emotion += 1
        emotions_summary = [
            {"emotion": e, "count": emotion_counts[e]}
            for e in ("Joy", "Love", "Anger", "Sadness", "Fear")
        ] + [{"emotion": "No explicit emotion", "count": no_emotion}]

        stage(90, "Generating dashboard...")
        aspects = self.aspect_service.aggregate(aspect_mentions)
        pros, cons = build_pros_cons(aspects, reviews)
        dist = build_distribution(reviews)
        verdict = build_verdict(reviews, aspects, quality.quality_score)
        processing_ms = int((time.perf_counter() - started) * 1000)
        statistics = build_statistics(
            reviews,
            exact_duplicates=dup_summary["duplicates_removed"],
            near_duplicates=dup_summary["near_duplicates_detected"],
            processing_ms=processing_ms,
            aspect_mention_total=sum(len(m) for m in aspect_mentions),
        )

        summary = {
            "source": source,
            "filename": filename,
            "detected_column": detected_column,
            "sentiment": dist.model_dump(),
            "confidence_histogram": build_confidence_histogram(reviews).model_dump(),
            "quality": quality.model_dump(),
            "aspects": [a.model_dump() for a in aspects],
            "pros": [p.model_dump() for p in pros],
            "cons": [c.model_dump() for c in cons],
            "most_discussed": [
                {"aspect": a.aspect, "percentage": a.positive_percentage,
                 "mention_count": a.mention_count, "average_confidence": a.average_confidence}
                for a in aspects[:8]
            ],
            "statistics": statistics.model_dump(),
            "verdict": verdict.model_dump(),
            "trust": trust,
            "emotions": emotions_summary,
        }
        store.put_reviews(analysis_id, reviews)
        stage(97, "Generating dashboard...")
        store.set_completed(analysis_id, summary)
        logger.info(
            "Analysis %s completed: %d reviews, source=%s, column=%s, %d ms",
            analysis_id, len(reviews), source, detected_column, processing_ms,
        )
        return {**store.get(analysis_id), "reviews": reviews}
