from __future__ import annotations
from collections import Counter

def build_schema(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {"columns": [], "column_types": {}}

    columns = list(rows[0].keys())
    column_types: dict[str, str] = {}

    for column in columns:
        detected_types = Counter(
            type(value).__name__ for value in (row.get(column) for row in rows) if value is not None
        )
        column_types[column] = detected_types.most_common(1)[0][0] if detected_types else "null"

    return {
        "columns": columns,
        "column_types": column_types,
    }

def build_preview(rows: list[dict[str, object]], limit: int = 20) -> list[dict[str, object]]:
    return rows[:limit]

def build_summary(
    rows: list[dict[str, object]],
    warnings_count: int,
    errors_count: int,
    aggregation: dict[str, object],
) -> dict[str, object]:
    return {
        "total_rows": len(rows),
        "valid_rows": max(len(rows) - errors_count, 0),
        "invalid_rows": errors_count,
        "warnings": warnings_count,
        "errors": errors_count,
        "aggregation": aggregation,
    }
