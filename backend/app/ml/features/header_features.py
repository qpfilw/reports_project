from __future__ import annotations
from difflib import SequenceMatcher
from typing import Any
from app.ml.utils.preprocessing import canonical_name, normalize_text, tokenize_text

def build_header_profile(headers: list[str]) -> dict[str, Any]:
    normalized_headers = [normalize_text(header) for header in headers if normalize_text(header)]
    return {
        "headers": headers,
        "normalized_headers": normalized_headers,
        "tokens": {header: tokenize_text(header) for header in headers},
        "canonical": {header: canonical_name(header) for header in headers},
        "column_count": len(headers),
    }

def calculate_header_similarity(left: str, right: str) -> float:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0

    left_tokens = set(tokenize_text(left_norm))
    right_tokens = set(tokenize_text(right_norm))
    token_similarity = 0.0
    if left_tokens or right_tokens:
        intersection = left_tokens & right_tokens
        union = left_tokens | right_tokens
        token_similarity = len(intersection) / len(union) if union else 0.0

    string_similarity = SequenceMatcher(None, left_norm, right_norm).ratio()
    canonical_similarity = SequenceMatcher(None, canonical_name(left_norm), canonical_name(right_norm)).ratio()
    return round(max(token_similarity, string_similarity * 0.85, canonical_similarity * 0.9), 4)