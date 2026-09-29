"""Export service: sanitized CSV / JSON downloads (spec section 44)."""
from __future__ import annotations

import csv
import io
import json

from security.file_security import sanitize_csv_cell


def _csv_response(rows: list[list], filename: str) -> tuple[bytes, str, str]:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8"), "text/csv; charset=utf-8", filename


def reviews_csv(reviews: list, analysis_id: str) -> tuple[bytes, str, str]:
    rows = [[
        "id", "review", "review_status", "review_probability", "relevance",
        "relevance_level", "sentiment", "confidence", "positive_probability",
        "negative_probability", "neutral_probability", "aspects",
        "suspicion_score", "suspicious", "suspicion_reasons",
        "contributing_terms", "duplicate", "near_duplicate",
    ]]
    for r in reviews:
        rows.append([
            r.id,
            sanitize_csv_cell(r.original_text),
            r.review_status.value,
            r.review_probability,
            r.relevance,
            r.relevance_level.value,
            r.sentiment.value,
            r.confidence,
            r.positive_probability,
            r.negative_probability,
            r.neutral_probability,
            sanitize_csv_cell("; ".join(f"{a.category}:{a.sentiment.value}" for a in r.aspects)),
            r.suspicion_score,
            "YES" if r.suspicious else "NO",
            sanitize_csv_cell("; ".join(r.suspicion_reasons)),
            sanitize_csv_cell(", ".join(r.contributing_terms)),
            "YES" if r.duplicate else "NO",
            "YES" if r.near_duplicate else "NO",
        ])
    return _csv_response(rows, f"reviews_{analysis_id}.csv")


def aspects_csv(aspects: list, analysis_id: str) -> tuple[bytes, str, str]:
    rows = [[
        "aspect", "mentions", "positive_count", "neutral_count", "negative_count",
        "positive_pct", "neutral_pct", "negative_pct", "avg_confidence", "overall",
    ]]
    for a in aspects:
        rows.append([
            sanitize_csv_cell(a.aspect), a.mention_count,
            a.positive_count, a.neutral_count, a.negative_count,
            a.positive_percentage, a.neutral_percentage, a.negative_percentage,
            a.average_confidence, a.overall.value,
        ])
    return _csv_response(rows, f"aspects_{analysis_id}.csv")


def quality_json(summary: dict) -> tuple[bytes, str, str]:
    payload = {
        "analysis_id": summary.get("analysis_id"),
        "quality": summary.get("quality"),
        "statistics": summary.get("statistics"),
    }
    return (
        json.dumps(payload, indent=2).encode("utf-8"),
        "application/json",
        f"quality_report_{summary.get('analysis_id')}.json",
    )


def metrics_json(metadata: dict) -> tuple[bytes, str, str]:
    return (
        json.dumps(metadata, indent=2, default=str).encode("utf-8"),
        "application/json",
        "model_metrics.json",
    )


def analysis_json(summary: dict, reviews: list) -> tuple[bytes, str, str]:
    payload = dict(summary)
    payload["reviews"] = [
        r.model_dump() for r in reviews
    ] if reviews else []
    return (
        json.dumps(payload, indent=2, default=str).encode("utf-8"),
        "application/json",
        f"analysis_{summary.get('analysis_id')}.json",
    )
