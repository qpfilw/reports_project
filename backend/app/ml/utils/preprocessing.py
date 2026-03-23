from __future__ import annotations
import re
import unicodedata
from collections.abc import Iterable

_NON_ALNUM_RE = re.compile(r"[^a-z0-9а-яё]+", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

_CANONICAL_SYNONYMS: dict[str, tuple[str, ...]] = {
    "date": ("дата", "date", "period", "период"),
    "amount": ("sum", "amount", "total", "итог", "сумм", "сумма", "стоимость"),
    "count": ("count", "qty", "quantity", "кол", "количество", "шт"),
    "id": ("id", "код", "code", "номер", "num"),
    "name": ("name", "title", "наименование", "название"),
    "department": ("department", "dept", "подразделение", "отдел"),
}

def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("_", " ")
    text = _NON_ALNUM_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()

def tokenize_text(value: object) -> list[str]:
    normalized = normalize_text(value)
    if not normalized:
        return []

    tokens = normalized.split(" ")
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        for canonical, variants in _CANONICAL_SYNONYMS.items():
            if token == canonical or token in variants:
                expanded.append(canonical)
    return list(dict.fromkeys(expanded))

def canonical_name(value: object) -> str:
    tokens = tokenize_text(value)
    if not tokens:
        return ""
    return "_".join(tokens)

def iter_unique_normalized(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_text(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
