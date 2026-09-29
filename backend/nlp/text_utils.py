"""NLTK resource bootstrap + shared regexes used across the NLP layer."""
from __future__ import annotations

import re

import nltk

_NLTK_RESOURCES = [
    ("tokenizers/punkt", "punkt"),
    ("tokenizers/punkt_tab", "punkt_tab"),
    ("corpora/stopwords", "stopwords"),
    ("corpora/wordnet", "wordnet"),
    ("corpora/omw-1.4", "omw-1.4"),
]

_checked = False


def ensure_nltk() -> None:
    """Download required NLTK resources once, on first use."""
    global _checked
    if _checked:
        return
    for find_path, name in _NLTK_RESOURCES:
        try:
            nltk.data.find(find_path)
        except LookupError:
            try:
                nltk.download(name, quiet=True)
            except Exception:
                pass  # offline environments fall back to regex tokenization paths
    _checked = True


URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")
EMAIL_RE = re.compile(r"\S+@\S+\.\S+")
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u2764]"
)
# Repeated-character collapse for LETTERS only ("gooood" -> "good");
# digits are excluded so meaningful numbers (5000mAh, ₹20000) survive.
REPEATED_CHAR_RE = re.compile(r"([a-zA-Z])\1{2,}")
# Meaningful product numbers: 5000mAh, 120Hz, 4K, 8 hours, ₹20000, 6.5 inch
MEANINGFUL_NUMBER_RE = re.compile(
    r"(?:[$₹€£]?\d+(?:[.,]\d+)?)(?:\s?(?:mah|ah|hz|khz|ghz|w|watt|watts|v|volt|volts|gb|tb|mb|inch|inches|in|hrs?|hours?|k|mp|mm|cm|km|x|percent|%|star|stars|yr|year|years?))?\b",
    re.IGNORECASE,
)
WHITESPACE_RE = re.compile(r"\s+")
SYMBOL_RE = re.compile(r"[^a-zA-Z0-9\s]")
ALPHA_RE = re.compile(r"[a-zA-Z]")
DIGIT_RE = re.compile(r"[0-9]")
