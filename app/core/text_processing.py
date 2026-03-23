import re
from collections import Counter

WORD_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9'-]*")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "with",
    "you",
    "your",
}


def tokenize_text(text: str) -> list[str]:
    """Normalize text into filtered lowercase words."""
    tokens = [match.group(0).lower() for match in WORD_PATTERN.finditer(text)]
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def count_words(words: list[str]) -> dict[str, int]:
    """Convert a word list into frequency counts."""
    return dict(Counter(words))
