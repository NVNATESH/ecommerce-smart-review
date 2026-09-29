"""Text preprocessing pipeline built on NLTK.

Design rules enforced here:

* meaningful numbers are preserved ("5000mAh", "120Hz", "4K", "8 hours");
* negation is preserved ("not good" -> "not_good") so TF-IDF keeps the flip;
* repeated characters are collapsed ("gooood" -> "good") while the original
  representation stays available for the suspicious-review signals;
* three text representations are produced per review:
    - original_text   (as provided)
    - normalized_text (cleaned, repetition-collapsed, readable)
    - model_text      (lower-cased, negation-joined, lemmatised, for TF-IDF)
"""
from __future__ import annotations

import html
import re
import string
from dataclasses import dataclass, field

from nlp.text_utils import (
    ALPHA_RE,
    DIGIT_RE,
    EMOJI_RE,
    HTML_TAG_RE,
    MEANINGFUL_NUMBER_RE,
    REPEATED_CHAR_RE,
    SYMBOL_RE,
    URL_RE,
    WHITESPACE_RE,
)
from nlp.text_utils import ensure_nltk  # re-exported for convenience
from nlp.tokenizer import is_negator, tokenize_words

_PUNCT_TABLE = str.maketrans("", "", string.punctuation.replace("'", ""))

try:
    from nltk.corpus import stopwords as _nltk_stopwords

    ensure_nltk()
    STOP_WORDS = set(_nltk_stopwords.words("english"))
except Exception:  # pragma: no cover - offline fallback
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
        "be", "been", "being", "to", "of", "in", "on", "for", "with", "at",
        "by", "from", "this", "that", "it", "its", "as", "i", "my", "me",
        "we", "our", "you", "your", "he", "she", "they", "them", "their",
    }

# Negators and contractions must survive stopword removal.
_STOP_WORDS = STOP_WORDS - {"not", "no", "nor", "never", "don", "doesn", "didn", "isn", "aren", "wasn", "weren", "won", "wouldn", "couldn", "shouldn", "haven", "hasn", "hadn", "ain"}

try:
    from nltk.stem import WordNetLemmatizer

    ensure_nltk()
    _LEMMA = WordNetLemmatizer()

    def _lemmatize(token: str) -> str:
        verb = _LEMMA.lemmatize(token, "v")
        return _LEMMA.lemmatize(verb, "n") if verb == token else verb
except Exception:  # pragma: no cover
    def _lemmatize(token: str) -> str:
        for suf in ("ing", "ed", "es", "s"):
            if token.endswith(suf) and len(token) > len(suf) + 2:
                return token[: -len(suf)]
        return token


@dataclass
class PreprocessedText:
    original_text: str
    normalized_text: str
    model_text: str
    tokens: list[str]
    emojis: list[str] = field(default_factory=list)
    word_count: int = 0

    @property
    def alphabetic_ratio(self) -> float:
        stripped = self.original_text.strip()
        if not stripped:
            return 0.0
        alpha = len(ALPHA_RE.findall(stripped))
        non_space = len([c for c in stripped if not c.isspace()])
        return alpha / non_space if non_space else 0.0

    @property
    def symbol_ratio(self) -> float:
        stripped = self.original_text.strip()
        if not stripped:
            return 0.0
        non_space = [c for c in stripped if not c.isspace()]
        symbols = len(SYMBOL_RE.findall(stripped))
        return symbols / len(non_space)


class TextPreprocessor:
    """Reusable preprocessor: instantiate once, reuse across requests."""

    def preprocess(self, text: str) -> PreprocessedText:
        original = text.strip()
        emojis = EMOJI_RE.findall(original)

        # 1) Structural cleaning -------------------------------------------------
        cleaned = HTML_TAG_RE.sub(" ", original)
        cleaned = URL_RE.sub(" ", cleaned)
        cleaned = cleaned.replace("&amp;", "&").replace("&quot;", '"')
        cleaned = html.unescape(cleaned)

        # 2) Normalised (human-readable) form ------------------------------------
        # collapse 3+ repeated characters to 2 ("gooood" -> "good"), then to 1
        # for the model form so TF-IDF sees canonical tokens.
        normalized = REPEATED_CHAR_RE.sub(r"\1\1", cleaned)
        normalized = re.sub(r"([!?.,])\1+", r"\1", normalized)
        normalized = WHITESPACE_RE.sub(" ", normalized).strip()

        # Words whose exaggeration we collapsed ("amaaazing" -> "amaazing"):
        # these get fully de-duplicated in the model form ("amazing").
        exaggerated = {
            w for w in re.findall(r"[a-zA-Z']+", cleaned)
            if re.search(r"([a-zA-Z])\1{2,}", w)
        }
        # membership is checked against the once-collapsed form (3+ -> 2),
        # which is what the token loop actually sees for these words
        exaggerated_collapsed = {
            re.sub(r"([a-zA-Z])\1{2,}", r"\1\1", w) for w in exaggerated
        }

        # 3) Model form -----------------------------------------------------------
        # protect meaningful numbers ("5000mah", "120hz", "4k", "8 hours")
        protected: dict[str, str] = {}
        for i, match in enumerate(MEANINGFUL_NUMBER_RE.findall(normalized)):
            placeholder = f"NUMTOK{i}"
            protected[placeholder] = match.strip().lower()
            normalized = normalized.replace(match, f" {placeholder} ", 1)

        model_tokens: list[str] = []
        tokens = tokenize_words(normalized.lower()) if normalized.strip() else []
        negate_next = False
        for tok in tokens:
            if tok.upper() in protected:
                model_tokens.append(protected[tok.upper()])
                continue
            if tok.isdigit() or all(ch in string.punctuation for ch in tok):
                if tok.isdigit():
                    model_tokens.append(tok)
                continue
            base = tok.translate(_PUNCT_TABLE) or tok
            if not base:
                continue
            if is_negator(base) or is_negator(tok):
                negate_next = True
                continue
            if base in _STOP_WORDS:
                if negate_next and base.isalpha():
                    model_tokens.append(f"not_{base}")  # keep scope of negation wide
                    negate_next = False
                continue
            if not base.isalpha() and not DIGIT_RE.search(base):
                continue
            if base.lower() in exaggerated_collapsed:
                base = re.sub(r"([a-zA-Z])\1+", r"\1", base)
            lemma = _lemmatize(base)
            if negate_next:
                model_tokens.append(f"not_{lemma}")
                negate_next = False
            else:
                model_tokens.append(lemma)

        model_text = " ".join(model_tokens)

        return PreprocessedText(
            original_text=original,
            normalized_text=normalized,
            model_text=model_text,
            tokens=model_tokens,
            emojis=emojis,
            word_count=len([t for t in normalized.split() if any(c.isalnum() for c in t)]),
        )

    def preprocess_batch(self, texts: list[str]) -> list[PreprocessedText]:
        return [self.preprocess(t) for t in texts]
