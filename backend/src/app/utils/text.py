from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Iterable


WHITESPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[^\w\s]")

CYRILLIC_TO_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "j",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "x",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sh",
        "ъ": "",
        "ы": "i",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        "ў": "o'",
        "қ": "q",
        "ғ": "g'",
        "ҳ": "h",
    }
)


def transliterate(text: str) -> str:
    return text.lower().translate(CYRILLIC_TO_LATIN)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    lowered = transliterate(text.replace("’", "'").replace("`", "'"))
    cleaned = PUNCT_RE.sub(" ", lowered)
    compact = WHITESPACE_RE.sub(" ", cleaned).strip()
    return compact


def extract_tokens(text: str | None) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [token for token in normalized.split(" ") if token]


def token_overlap_score(text: str, candidates: Iterable[str]) -> float:
    text_tokens = set(extract_tokens(text))
    if not text_tokens:
        return 0.0
    candidate_tokens = set()
    for candidate in candidates:
        candidate_tokens.update(extract_tokens(candidate))
    if not candidate_tokens:
        return 0.0
    return len(text_tokens & candidate_tokens) / max(len(text_tokens | candidate_tokens), 1)


def keyword_hit_score(text: str, terms: Iterable[str]) -> float:
    normalized = normalize_text(text)
    if not normalized:
        return 0.0
    hits = 0
    total = 0
    for term in terms:
        norm_term = normalize_text(term)
        if not norm_term:
            continue
        total += 1
        if norm_term in normalized:
            hits += 1
    return hits / total if total else 0.0


def sequence_similarity(text: str, other: str) -> float:
    if not text or not other:
        return 0.0
    return SequenceMatcher(a=normalize_text(text), b=normalize_text(other)).ratio()


def best_similarity(text: str, candidates: Iterable[str]) -> float:
    return max((sequence_similarity(text, candidate) for candidate in candidates), default=0.0)


def top_terms(text: str, limit: int = 8) -> list[str]:
    counter = Counter(extract_tokens(text))
    return [term for term, _ in counter.most_common(limit)]
