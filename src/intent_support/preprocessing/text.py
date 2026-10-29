"""Unicode normalization, explicit tokenization, and POS-aware lemmatization."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import nltk
from nltk.stem import WordNetLemmatizer
from sklearn.base import BaseEstimator, TransformerMixin

ROOT = Path(__file__).resolve().parents[3]
NLTK_DATA = ROOT / "data" / "nltk_data"
TOKEN_RE = re.compile(r"\{\{[^{}]+\}\}|[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", re.IGNORECASE)
NEGATIONS = {"not", "no", "never", "cannot", "n't"}
PROTECTED = NEGATIONS | {"us"}


def ensure_nltk_data() -> None:
    path = str(NLTK_DATA)
    if path not in nltk.data.path:
        nltk.data.path.insert(0, path)
    required = (
        "corpora/wordnet.zip",
        "taggers/averaged_perceptron_tagger_eng",
    )
    for resource in required:
        try:
            nltk.data.find(resource)
        except LookupError as exc:
            raise RuntimeError(
                f"Missing NLTK resource {resource}; run python3 scripts/setup_nltk_data.py"
            ) from exc


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("’", "'").casefold()
    text = re.sub(r"\bwon't\b", "will not", text)
    text = re.sub(r"\bcan't\b", "can not", text)
    text = re.sub(r"\bcannot\b", "can not", text)
    text = re.sub(r"\b([a-z]+)n't\b", r"\1 not", text)
    return re.sub(r"\s+", " ", text).strip()


def regex_tokens(text: str) -> list[str]:
    tokens = []
    for match in TOKEN_RE.findall(text):
        if match.startswith("{{"):
            slot = re.sub(r"[^a-z0-9]+", "_", match[2:-2].casefold()).strip("_")
            tokens.append(f"slot_{slot}")
        else:
            tokens.append(match)
    return tokens


def _wordnet_pos(tag: str) -> str | None:
    if tag.startswith("J"):
        return "a"
    if tag.startswith("V"):
        return "v"
    if tag.startswith("N"):
        return "n"
    if tag.startswith("R"):
        return "r"
    return None


class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Return token lists so vectorizers never run a hidden tokenizer."""

    def __init__(self, normalize: bool = True, tokenizer: str = "regex", lemmatize: bool = True):
        self.normalize = normalize
        self.tokenizer = tokenizer
        self.lemmatize = lemmatize

    def fit(self, X, y=None):
        if self.tokenizer not in {"regex", "whitespace"}:
            raise ValueError("tokenizer must be regex or whitespace")
        return self

    def transform(self, X):
        if self.lemmatize:
            ensure_nltk_data()
            lemmatizer = WordNetLemmatizer()
        output = []
        for text in X:
            if not isinstance(text, str):
                raise TypeError("TextPreprocessor expects strings")
            prepared = normalize_text(text) if self.normalize else text
            tokens = regex_tokens(prepared) if self.tokenizer == "regex" else prepared.split()
            if self.lemmatize and tokens:
                tagged = nltk.pos_tag(tokens, lang="eng")
                tokens = [
                    token if token.casefold() in PROTECTED or not pos or not token.isalpha()
                    else lemmatizer.lemmatize(token, pos)
                    for token, pos in ((word, _wordnet_pos(tag)) for word, tag in tagged)
                ]
            output.append(tokens)
        return output


def identity_tokens(tokens: list[str]) -> list[str]:
    """Pickle-safe tokenizer hook for CountVectorizer/TfidfVectorizer."""
    return tokens
