from __future__ import annotations
from collections.abc import Iterable

_EMPTY_VALUES = {None, "", "-", "—"}

def _clean_key(raw_key: object, index: int) -> str:
    key = str(raw_key).strip() if raw_key is not None else ""
    return key or f"column_{index + 1}"

def _clean_value(value: object) -> object:
    if isinstance(value, str):
        normalized = " ".join(value.replace("\xa0", " ").split())
        return normalized
    return value

def drop_empty_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    cleaned_rows: list[dict[str, object]] = []

    for row in rows:
        normalized_row = {
            _clean_key(key, index): _clean_value(value)
            for index, (key, value) in enumerate(row.items())
        }
        if any(value not in _EMPTY_VALUES for value in normalized_row.values()):
            cleaned_rows.append(normalized_row)

    return cleaned_rows
