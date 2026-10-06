"""Emotion lexicon — lightweight lexicon-based emotion detection over reviews.
Each emotion maps to a set of cue words; a review can express multiple emotions.
Deliberately lexicon-based (no new model) so it adds zero latency to inference."""
from __future__ import annotations

import re

EMOTION_LEXICON = {
    "Joy": {
        "love", "loved", "loving", "happy", "happiness", "glad", "delighted",
        "wonderful", "fantastic", "awesome", "great", "excellent", "amazing",
        "perfect", "superb", "brilliant", "joy", "joyful", "pleased", "excited",
        "thrilled", "best", "enjoy", "enjoyed", "enjoying",
    },
    "Anger": {
        "angry", "angrier", "furious", "outraged", "outrageous", "hate", "hated",
        "annoying", "annoyed", "frustrating", "frustrated", "frustration",
        "ridiculous", "unacceptable", "pathetic", "worst", "useless", "garbage",
        "trash", "junk", "rude", "scam", "cheated", "waste",
    },
    "Sadness": {
        "sad", "sadly", "disappointed", "disappointing", "disappointment",
        "unfortunately", "regret", "regretted", "sorrow", "unhappy", "upset",
        "depressed", "heartbroken", "cried", "miss", "missed", "poor",
    },
    "Fear": {
        "afraid", "fear", "fearful", "scared", "scary", "worried", "worry",
        "worrying", "anxious", "anxiety", "nervous", "risk", "risky", "dangerous",
        "unsafe", "concerned", "concern", "doubt", "doubtful",
    },
    "Love": {
        "adore", "adored", "cherish", "cherished", "favourite", "favorite",
        "obsessed", "smitten", "recommend", "recommended", "impressed",
        "impressive", "stunning", "beautiful", "perfect",
    },
}


def detect_emotions(text: str) -> dict[str, bool]:
    """Returns {emotion: present?} for one review (case-insensitive word match)."""
    words = set(re.findall(r"[a-z']+", text.lower()))
    return {emotion: bool(words & cues) for emotion, cues in EMOTION_LEXICON.items()}
