"""Aspect service: clause-level ABSA per review + dataset-level aggregation."""
from __future__ import annotations

from nlp.aspect_engine import AspectMention, analyze as analyze_text
from schemas.analysis import AspectSummary


class AspectService:
    def analyze_review(self, original_text: str) -> tuple[list[AspectMention], list]:
        """Returns (aspect mentions, clause analyses) for one review."""
        return analyze_text(original_text)

    @staticmethod
    def aggregate(mentions_per_review: list[list[AspectMention]]) -> list[AspectSummary]:
        stats: dict[str, dict] = {}
        for mentions in mentions_per_review:
            for m in mentions:
                s = stats.setdefault(
                    m.category,
                    {"mention_count": 0, "Positive": 0, "Neutral": 0, "Negative": 0,
                     "Mixed": 0, "confidence_sum": 0.0},
                )
                s["mention_count"] += 1
                s[m.sentiment] += 1
                s["confidence_sum"] += m.confidence

        summaries: list[AspectSummary] = []
        for category, s in stats.items():
            n = s["mention_count"]
            def pct(key: str) -> float:
                return round(s[key] / n * 100, 1) if n else 0.0
            if s["Positive"] > s["Negative"]:
                overall = "Positive"
            elif s["Negative"] > s["Positive"]:
                overall = "Negative"
            elif s["Mixed"] and s["Mixed"] >= max(s["Positive"], s["Negative"]):
                overall = "Mixed"
            else:
                overall = "Neutral"
            summaries.append(AspectSummary(
                aspect=category,
                mention_count=n,
                positive_count=s["Positive"],
                neutral_count=s["Neutral"] + s["Mixed"],
                negative_count=s["Negative"],
                positive_percentage=pct("Positive"),
                neutral_percentage=pct("Neutral"),
                negative_percentage=pct("Negative"),
                average_confidence=round(s["confidence_sum"] / n, 3) if n else 0.0,
                overall=overall,
            ))
        summaries.sort(key=lambda a: a.mention_count, reverse=True)
        return summaries
