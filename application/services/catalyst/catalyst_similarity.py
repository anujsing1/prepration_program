"""Fuzzy matching utilities for catalyst deduplication."""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def normalize_catalyst_token(value: str) -> str:
    """Normalize catalyst code/name for comparison."""
    cleaned = re.sub(r"[^a-z0-9]+", "", value.lower())
    for suffix in ("win", "award", "order", "deal", "news"):
        if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 2:
            cleaned = cleaned[: -len(suffix)]
    return cleaned


def similarity_score(left: str, right: str) -> float:
    """Return similarity in [0, 1] between two catalyst strings."""
    left_norm = normalize_catalyst_token(left)
    right_norm = normalize_catalyst_token(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def find_best_match(
    query: str,
    candidates: list[tuple[str, str]],
    *,
    threshold: float = 0.85,
) -> list[tuple[str, float, str]]:
    """Find candidates above threshold. Each item is (code, score, source)."""
    results: list[tuple[str, float, str]] = []
    for code, source in candidates:
        score = max(similarity_score(query, code), similarity_score(query, code.replace("_", " ")))
        if score >= threshold:
            results.append((code, score, source))
    results.sort(key=lambda item: item[1], reverse=True)
    return results
