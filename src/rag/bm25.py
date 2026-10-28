"""BM25 keyword scoring for Vietnamese forum text, standard library only."""

import math
import re
import unicodedata
from collections import Counter

K1 = 1.5
B = 0.75

_WORD = re.compile(r"\w+")


def fold(text: str) -> str:
    """Lowercase and strip Vietnamese diacritics, so "Học" and "hoc" match."""
    text = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def tokenize(text: str) -> list[str]:
    """Accent-folded syllables plus adjacent-syllable bigrams.

    Most Vietnamese words have two syllables ("học sinh"), so bigrams stand in for word segmentation.
    """
    syllables = _WORD.findall(fold(text))
    return syllables + [f"{a}_{b}" for a, b in zip(syllables, syllables[1:])]


def bm25_scores(query: str, documents: list[str]) -> list[float]:
    """Score every document against the query with Okapi BM25."""
    docs = [Counter(tokenize(d)) for d in documents]
    if not docs:
        return []
    lengths = [sum(d.values()) for d in docs]
    avgdl = sum(lengths) / len(docs) or 1.0

    scores = [0.0] * len(docs)
    for term in set(tokenize(query)):
        df = sum(1 for d in docs if term in d)
        if not df:
            continue
        idf = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
        for i, d in enumerate(docs):
            tf = d.get(term, 0)
            if tf:
                scores[i] += idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * lengths[i] / avgdl))
    return scores
