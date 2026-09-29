"""Aspect-Based Sentiment Analysis engine.

Rule-based, explainable ABSA:

1. The review is split into clauses (sentence punctuation and contrastive
   conjunctions like "but", "however", "although").
2. Each clause is matched against aspect synonym patterns (battery life ->
   Battery, screen -> Display, ...).
3. Opinion words inside the same clause decide the aspect sentiment, so
   "The battery is amazing but the camera is terrible" yields
   Battery -> Positive and Camera -> Negative.
4. Clauses with aspects but no opinion words become Neutral (lower confidence);
   the overall review label is never copied onto every aspect.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Canonical category -> synonym patterns (matched with word boundaries, lowercase).
ASPECT_PATTERNS: dict[str, list[str]] = {
    "Battery": [r"battery(?![-\w])", r"battery\s+life", r"battery\s+backup", r"charge\s+life", r"juice"],
    "Camera": [r"camera", r"cam\s+quality", r"photo(?!s?\s+shop)", r"photos?", r"selfie", r"lens", r"megapixel", r"\d+\s*mp\b"],
    "Display": [r"display", r"screen", r"touchscreen", r"refresh\s+rate", r"resolution", r"amoled", r"lcd", r"oled", r"brightness"],
    "Sound": [r"sound", r"audio", r"speaker(s)?", r"bass", r"volume", r"loudness", r"headphone\s+jack", r"sound\s+quality"],
    "Microphone": [r"mic\b", r"microphone", r"mic\s+quality", r"voice\s+pickup"],
    "Charging": [r"charg(e|er|ing)", r"fast\s+charg", r"charging\s+speed", r"adapter", r"usb[-\s]?c", r"type[-\s]?c", r"wireless\s+charg"],
    "Performance": [r"performance", r"speed", r"lag(s|gy|ging)?", r"slow(s|ed)?", r"smooth(ly)?", r"stutter", r"freez(e|es|ing)", r"multitask", r"benchmark"],
    "Price": [r"price", r"cost(s|ly)?", r"expensive", r"cheap", r"affordable", r"overpriced", r"value\s+for\s+money", r"worth\s+the\s+money", r"budget"],
    "Delivery": [r"delivery", r"shipp(ing|ed)", r"packag(ing|e)\s+(arrived|was|is)", r"arriv(e|ed|al)", r"courier", r"dispatch"],
    "Build Quality": [r"build\s+quality", r"build", r"hous(ing|e)", r"material", r"sturdy", r"flimsy", r"plasticky", r"premium\s+feel"],
    "Design": [r"design", r"look(s)?", r"appearance", r"aesthetic", r"colour(s)?", r"color(s)?", r"style", r"slim", r"sleek"],
    "Heating": [r"heat(s|ing|ed)?", r"overheat(s|ing|ed)?", r"gets?\s+hot", r"throttl"],
    "Keyboard": [r"keyboard", r"key(s)?\s+(feel|travel)", r"keys", r"trackpad", r"touchpad", r"typ(e|ing)\s+experience"],
    "Mouse": [r"mouse", r"cursor", r"click(s)?\s+(of\s+the\s+)?mouse", r"scroll\s+wheel"],
    "Software": [r"software", r"firmware", r"os\b", r"user\s+interface", r"\bui\b", r"update(s)?", r"app(s)?\s+(crash|keep|is|are)", r"bloatware", r"bugs?"],
    "Storage": [r"storage", r"\d+\s*(gb|tb)\s+(of\s+)?storage", r"memory\s+card", r"sd\s+card", r"internal\s+memory", r"ram"],
    "Processor": [r"processor", r"cpu", r"chipset", r"snapdragon", r"exynos", r"mediatek", r"core\s+i\d", r"ryzen", r"m1|m2|m3\b", r"clock\s+speed"],
    "Durability": [r"durab(le|ility)", r"last(s|ed)?\s+(long|years?|months?)", r"longevity", r"warranty", r"broke? (easily|within)", r"wear\s+and\s+tear", r"water\s+resistan", r"scratch"],
}

_ASPECT_RES: dict[str, list[re.Pattern]] = {
    cat: [re.compile(rf"\b{p}", re.IGNORECASE) for p in pats]
    for cat, pats in ASPECT_PATTERNS.items()
}

# Clause boundaries: sentence punctuation + contrastive conjunctions.
CLAUSE_SPLIT_RE = re.compile(
    r"(?<=[.!?;])\s+|,\s*(?:but|though|although|however|yet)\b|\s+\b(?:but|however|although|though|yet|whereas|while)\b\s+",
    re.IGNORECASE,
)

STRONG_POS = {"excellent", "amazing", "perfect", "outstanding", "superb", "best", "fantastic", "incredible", "brilliant", "love", "loved", "impressive"}
STRONG_NEG = {"terrible", "awful", "worst", "horrible", "pathetic", "useless", "garbage", "hate", "hated", "disaster", "unusable", "defective", "broken"}

POS_WORDS = STRONG_POS | {
    "good", "great", "nice", "solid", "decent", "impressed", "impressive",
    "smooth", "sharp", "crisp", "bright", "fast", "quick", "reliable",
    "worth", "worthy", "sturdy", "beautiful", "clear", "loud", "comfortable",
    "happy", "satisfied", "pleased", "responsive", "efficient", "durable",
    "long", "snappy", "premium", "stunning", "gorgeous", "clean", "value",
    # common real-review praise words the base lexicon missed
    "sleek", "elegant", "neat", "comfy", "handy", "flawless", "spotless",
    "generous", "spacious", "sturdy", "convenient", "thoughtful", "fair",
}
NEG_WORDS = STRONG_NEG | {
    "bad", "poor", "disappointing", "disappointed", "disappointment", "slow",
    "laggy", "lag", "lags", "weak", "dull", "dim", "faint", "blurry", "low",
    "noisy", "unclear", "unreliable", "uncomfortable", "unhappy",
    "dissatisfied", "frustrating", "annoying", "waste", "flimsy", "fragile",
    "overpriced", "expensive", "drain", "drains", "draining", "dead",
    "stopped", "failed", "fails", "issue", "issues", "problem", "problems",
    "buggy", "crash", "crashes", "crashed", "heating", "overheating", "hot",
    "scratched", "scratches", "cracked", "cheap", "plasticky", "mediocre",
    # common real-review complaint verbs/adjectives the base lexicon missed
    "heats", "overheats", "unresponsive", "rude", "crackles", "crackling",
    "distorts", "distorted", "swollen", "flickers", "flickering", "throttles",
    "unusable", "defect", "defective", "malfunctioning", "malfunctioned",
    "unacceptable", "pathetic", "hopeless", "worthless", "junk", "damaged",
}

INTENSIFIERS = {"very", "really", "extremely", "super", "so", "totally", "absolutely", "incredibly", "highly", "quite"}


@dataclass
class AspectMention:
    category: str
    sentiment: str  # Positive | Negative | Neutral
    confidence: float


@dataclass
class ClauseAnalysis:
    clause: str
    aspects: list[str]
    sentiment: str
    confidence: float


def detect_aspects(text: str) -> list[str]:
    """All aspect categories mentioned anywhere in the text (de-duplicated, ordered)."""
    found: list[str] = []
    for cat, patterns in _ASPECT_RES.items():
        if any(p.search(text) for p in patterns):
            found.append(cat)
    return found


def split_clauses(text: str) -> list[str]:
    clauses = [c.strip() for c in CLAUSE_SPLIT_RE.split(text) if c and c.strip()]
    return clauses or ([text.strip()] if text.strip() else [])


def _clause_sentiment(clause: str) -> tuple[str, float]:
    lower = clause.lower()
    tokens = re.findall(r"[a-z']+", lower)
    pos_hits = [t for t in tokens if t in POS_WORDS]
    neg_hits = [t for t in tokens if t in NEG_WORDS]
    has_intensifier = any(t in INTENSIFIERS for t in tokens)

    # Negation check: "not good", "never works" flip within a small window.
    def negated(word_idx: int, tokens: list[str]) -> bool:
        window = tokens[max(0, word_idx - 3):word_idx]
        return any(t in {"not", "no", "never", "n't", "don't", "dont", "doesn't", "doesnt", "isn't", "isnt", "didn't", "didnt", "won't", "wont", "can't", "cant"} for t in window)

    pos_count = sum(1 for i, t in enumerate(tokens) if t in POS_WORDS and not negated(i, tokens))
    neg_count = sum(1 for i, t in enumerate(tokens) if t in NEG_WORDS and not negated(i, tokens))
    # negated positive words act as negatives ("not good")
    neg_count += sum(1 for i, t in enumerate(tokens) if t in POS_WORDS and negated(i, tokens))
    # negated negative words act as mildly positive ("never lags")
    pos_count += sum(1 for i, t in enumerate(tokens) if t in NEG_WORDS and negated(i, tokens))

    if pos_count > neg_count:
        base = 0.86 if any(t in STRONG_POS for t in tokens) else 0.75
        return "Positive", min(0.97, base + (0.06 if has_intensifier else 0.0))
    if neg_count > pos_count:
        base = 0.88 if any(t in STRONG_NEG for t in tokens) else 0.76
        return "Negative", min(0.97, base + (0.06 if has_intensifier else 0.0))
    if pos_count and pos_count == neg_count:
        return "Mixed", 0.62
    return "Neutral", 0.60


def analyze(text: str) -> tuple[list[AspectMention], list[ClauseAnalysis]]:
    """Return per-aspect mentions and per-clause sentiment for a single review."""
    mentions: list[AspectMention] = []
    clause_analyses: list[ClauseAnalysis] = []
    seen: set[tuple[str, str]] = set()

    for clause in split_clauses(text):
        if not clause:
            continue
        cats = detect_aspects(clause)
        sentiment, confidence = _clause_sentiment(clause)
        clause_analyses.append(ClauseAnalysis(clause, cats, sentiment, confidence))
        for cat in cats:
            key = (cat, sentiment)
            if key in seen:
                continue
            seen.add(key)
            mentions.append(AspectMention(category=cat, sentiment=sentiment, confidence=round(confidence, 3)))

    # Aspects mentioned but never tied to a clause with a polarity become Neutral.
    for cat in detect_aspects(text):
        if not any(m.category == cat for m in mentions):
            mentions.append(AspectMention(category=cat, sentiment="Neutral", confidence=0.60))

    return mentions, clause_analyses


def review_level_sentiment(clause_analyses: list[ClauseAnalysis]) -> tuple[str, float]:
    """Transparent aggregation of clause polarities into one review label."""
    pos = sum(1 for c in clause_analyses if c.sentiment == "Positive")
    neg = sum(1 for c in clause_analyses if c.sentiment == "Negative")
    neu = sum(1 for c in clause_analyses if c.sentiment == "Neutral")
    mixed = sum(1 for c in clause_analyses if c.sentiment == "Mixed")

    if not clause_analyses:
        return "Neutral", 0.5
    total = len(clause_analyses)
    if pos and neg and abs(pos - neg) <= 1:
        return "Mixed", max(0.62, 0.6 + 0.05 * min(pos, neg))
    if pos > neg:
        return "Positive", min(0.95, 0.65 + 0.1 * (pos - neg) / total)
    if neg > pos:
        return "Negative", min(0.95, 0.65 + 0.1 * (neg - pos) / total)
    if mixed:
        return "Mixed", 0.62
    return "Neutral", 0.6 + 0.05 * neu
