"""Sentiment service: model probabilities, confidence and Mixed handling.

Label decisions are transparent and documented:

1. Base label = argmax of the trained model's class probabilities.
2. Clause-evidence blending (spec sections 31/63): the aspect engine's
   clause-level polarities are a second, independent signal. When a review
   contains polar clauses, a small weight (lambda per clause, capped) is
   added to the matching class probabilities and the distribution is
   renormalised. This repairs the common real-data failure where an
   opinion-heavy but aspect-anchored review ("the keyboard feels flimsy")
   lands on Neutral, while never moving a review the model is confidently
   sure about and the clauses do not contradict.
3. Mixed rule: after blending, if Positive and Negative clauses both exist
   and the top-two margin is narrow (or the clause counts are balanced and
   the model is not confident), the review is Mixed instead of forcing one
   polarity onto contradictory text.
4. Neutral rule: when NO polar clause exists (purely factual statements like
   "it has 128GB storage") and the model is uncertain, the review is labelled
   Neutral. Neutral evidence is never fabricated from clause absence alone
   for confident predictions.

Displayed probabilities are the blended ones, so the label is always the
argmax of what the UI shows. Confidence = max blended probability: model
certainty informed by aspect evidence — not a guarantee of correctness.
"""
from __future__ import annotations

from ml.model_manager import ModelManager
from ml.sentiment_model import SentimentEngine


class SentimentService:
    CLAUSE_EVIDENCE_LAMBDA = 0.20   # weight per polar clause (capped at 2)
    MAX_POLAR_CLAUSES = 2
    MIXED_MARGIN = 0.15             # top-two gap below which contradiction -> Mixed
    MIXED_MAX_CONF = 0.80           # balanced clauses + this little model confidence -> Mixed
    NEUTRAL_FLIP_MAX_CONF = 0.68    # model this unsure with no polar clauses...
    NEUTRAL_FLIP_MIN_NEU = 0.20     # ...and at least this much Neutral probability
    EMOJI_NUDGE = 0.20              # virtual-clause weight for wordless emoji reviews
    EMOJI_NUDGE_MAX_CONF = 0.60     # ...only when the model is this unsure

    def __init__(self, manager: ModelManager):
        self.engine = SentimentEngine(manager.sentiment_model, manager.sentiment_vectorizer)

    def score(self, model_texts: list[str], clause_analyses_per_review: list,
              emoji_signals: list[dict] | None = None) -> list[dict]:
        probas = self.engine.predict_proba(model_texts)
        signals = emoji_signals or [None] * len(probas)
        results = []
        for row, clause_analyses, signal in zip(probas, clause_analyses_per_review, signals):
            probs = {
                label: float(row[self.engine.class_index(label)])
                for label in ("Positive", "Negative", "Neutral")
            }
            pos_clauses = sum(1 for c in clause_analyses if c.sentiment == "Positive")
            neg_clauses = sum(1 for c in clause_analyses if c.sentiment == "Negative")

            # 2) blend polar clause evidence into the class probabilities
            polar = min(pos_clauses + neg_clauses, self.MAX_POLAR_CLAUSES)
            if polar > 0:
                lam = self.CLAUSE_EVIDENCE_LAMBDA * polar
                share_pos = pos_clauses / (pos_clauses + neg_clauses)
                p_pos = probs["Positive"] + lam * share_pos
                p_neg = probs["Negative"] + lam * (1.0 - share_pos)
                total = p_pos + p_neg + probs["Neutral"]
                probs = {
                    "Positive": p_pos / total,
                    "Negative": p_neg / total,
                    "Neutral": probs["Neutral"] / total,
                }

            label = max(probs, key=probs.get)
            top2 = sorted(probs.values(), reverse=True)
            margin = top2[0] - top2[1] if len(top2) > 1 else 1.0

            # 3) Mixed handling for contradictory reviews
            if pos_clauses and neg_clauses:
                balanced = min(pos_clauses, neg_clauses) >= 1 and abs(pos_clauses - neg_clauses) <= 1
                if margin < self.MIXED_MARGIN or (balanced and max(probs.values()) < self.MIXED_MAX_CONF):
                    label = "Mixed"
            # 4) Neutral for uncertain, purely factual reviews; wordless emoji
            #    reviews keep their emoji signal (treated as virtual clauses)
            elif not pos_clauses and not neg_clauses:
                e_pos = min(int(signal["pos"]) if signal else 0, 2)
                e_neg = min(int(signal["neg"]) if signal else 0, 2)
                if max(probs.values()) < self.NEUTRAL_FLIP_MAX_CONF and probs["Neutral"] >= self.NEUTRAL_FLIP_MIN_NEU:
                    label = "Neutral"
                elif (e_pos or e_neg) and e_pos != e_neg and max(probs.values()) < self.EMOJI_NUDGE_MAX_CONF:
                    lam = self.EMOJI_NUDGE * max(e_pos, e_neg)
                    share = e_pos / (e_pos + e_neg)
                    p_pos = probs["Positive"] + lam * share
                    p_neg = probs["Negative"] + lam * (1.0 - share)
                    total = p_pos + p_neg + probs["Neutral"]
                    probs = {
                        "Positive": p_pos / total,
                        "Negative": p_neg / total,
                        "Neutral": probs["Neutral"] / total,
                    }
                    label = max(probs, key=probs.get)

            # 5) emoji nudge: reviews that express feeling ONLY through emojis
            #    (no words, no clauses) keep that signal when the model is unsure
            if signal and not pos_clauses and not neg_clauses:
                e_pos, e_neg = signal["pos"], signal["neg"]
                if (e_pos or e_neg) and max(probs.values()) < self.EMOJI_NUDGE_MAX_CONF and e_pos != e_neg:
                    lam = self.EMOJI_NUDGE * max(e_pos, e_neg)
                    if e_pos > e_neg:
                        probs["Positive"] += lam
                    else:
                        probs["Negative"] += lam
                    total = probs["Positive"] + probs["Negative"] + probs["Neutral"]
                    probs = {k: v / total for k, v in probs.items()}
                    label = max(probs, key=probs.get)

            results.append({
                "sentiment": label,
                "confidence": round(max(probs.values()), 4),
                "positive_probability": round(probs["Positive"], 4),
                "negative_probability": round(probs["Negative"], 4),
                "neutral_probability": round(probs["Neutral"], 4),
            })
        return results
