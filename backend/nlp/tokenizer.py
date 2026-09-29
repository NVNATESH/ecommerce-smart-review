"""Low-level tokenization helpers built on NLTK."""
from __future__ import annotations

import re

import nltk

from nlp.text_utils import ensure_nltk

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Words that flip the polarity of what follows them.
NEGATORS = {
    "not", "no", "never", "none", "nobody", "nothing", "neither", "nor",
    "cannot", "can't", "cant", "don't", "dont", "doesn't", "doesnt",
    "didn't", "didnt", "isn't", "isnt", "aren't", "arent", "wasn't",
    "wasnt", "weren't", "werent", "won't", "wont", "wouldn't", "wouldnt",
    "couldn't", "couldnt", "shouldn't", "shouldnt", "haven't", "havent",
    "hasn't", "hasnt", "hadn't", "hadnt",
}


def tokenize_words(text: str) -> list[str]:
    ensure_nltk()
    return nltk.word_tokenize(text)


def tokenize_sentences(text: str) -> list[str]:
    ensure_nltk()
    return nltk.sent_tokenize(text)


def is_negator(token: str) -> bool:
    return token.lower() in NEGATORS
