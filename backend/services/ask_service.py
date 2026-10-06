"""Ask-the-Reviews: question answering over a completed analysis.

Aspect routing + TF-IDF retrieval + template answer synthesis — no external
LLM/API, works fully offline. The retrieval index is built lazily once per
analysis and cached (LRU-capped) so repeated questions answer in milliseconds
and memory stays bounded."""
from __future__ import annotations

import threading

from sklearn.feature_extraction.text import TfidfVectorizer

from nlp.aspect_engine import detect_aspects
from nlp.preprocessing import TextPreprocessor


class AskService:
    MAX_INDEXED = 25

    def __init__(self):
        self._index = {}
        self._order = []
        self._lock = threading.Lock()
        self._pre = TextPreprocessor()

    def _index_for(self, analysis_id, reviews):
        with self._lock:
            if analysis_id not in self._index:
                vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
                matrix = vec.fit_transform([r.normalized_text for r in reviews])
                self._index[analysis_id] = (vec, matrix)
                self._order.append(analysis_id)
                while len(self._order) > self.MAX_INDEXED:
                    self._index.pop(self._order.pop(0), None)
            return self._index[analysis_id]

    def ask(self, analysis_id: str, question: str, reviews: list, record: dict | None = None):
        vec, matrix = self._index_for(analysis_id, reviews)
        q_model = self._pre.preprocess(question).model_text.strip()
        q_vec = vec.transform([q_model or question.lower()])
        sims = (matrix @ q_vec.T).toarray().ravel()

        q_aspects = detect_aspects(question)
        general = any(k in question.lower() for k in ("overall", "summar", "verdict", "general", "opinion"))
        if q_aspects:
            aspect_name = " / ".join(q_aspects)
        elif general:
            aspect_name = "the product"
        else:
            aspect_name = "the product"

        # general/overall questions: answer from the dataset-level summary
        if general and not q_aspects and record:
            v = record.get("verdict", {})
            s = record.get("sentiment", {})
            qly = record.get("quality", {})
            return {
                "question": question,
                "answer": (
                    f"Overall verdict: {v.get('overall_sentiment')}. {v.get('statement')} "
                    f"Dataset quality: {qly.get('quality_score')}/100 ({qly.get('dataset_decision')})."
                ),
                "matched": total if (total := len(reviews)) else 0,
                "breakdown": {
                    "Positive": s.get("positive", 0),
                    "Negative": s.get("negative", 0),
                    "Neutral": s.get("neutral", 0),
                },
                "quotes": [],
            }

        matched_idx = []
        for i, r in enumerate(reviews):
            aspect_hit = bool(q_aspects) and any(a.category in q_aspects for a in r.aspects)
            if aspect_hit or sims[i] >= 0.05:
                matched_idx.append((sims[i] + (0.5 if aspect_hit else 0.0), i))
        matched_idx.sort(reverse=True)
        matched = [reviews[i] for _, i in matched_idx[:10]]

        total = len(reviews)
        if not matched:
            return {
                "question": question,
                "answer": (
                    f"No reviews in this analysis mention {aspect_name}. "
                    "Try asking about: Battery, Camera, Display, Sound, Delivery, Price, Heating, Performance."
                ),
                "matched": 0,
                "breakdown": {"Positive": 0, "Negative": 0, "Neutral": 0},
                "quotes": [],
            }

        pos = sum(1 for r in matched if r.sentiment.value == "Positive")
        neg = sum(1 for r in matched if r.sentiment.value == "Negative")
        neu = len(matched) - pos - neg
        pos_pct = pos / len(matched) * 100
        neg_pct = neg / len(matched) * 100
        if pos_pct >= 60:
            tone = f"Overall, customers are happy with {aspect_name}."
        elif neg_pct >= 60:
            tone = f"Overall, {aspect_name} is the most common complaint."
        else:
            tone = f"Opinions on {aspect_name} are mixed."

        answer = (
            f"{len(matched)} of {total} reviews mention {aspect_name}: "
            f"{pos_pct:.0f}% positive, {neg_pct:.0f}% negative. {tone}"
        )
        quotes = [
            {
                "id": r.id,
                "text": r.original_text,
                "sentiment": r.sentiment.value,
                "confidence": r.confidence,
            }
            for r in matched[:3]
        ]
        return {
            "question": question,
            "answer": answer,
            "matched": len(matched),
            "breakdown": {"Positive": pos, "Negative": neg, "Neutral": neu},
            "quotes": quotes,
        }
