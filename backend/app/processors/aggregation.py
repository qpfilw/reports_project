from __future__ import annotations

def build_aggregation(rows: list[dict[str, object]]) -> dict[str, object]:
    if not rows:
        return {"columns": 0, "rows": 0, "numeric_columns": {}}

    headers = list(rows[0].keys())
    numeric_columns: dict[str, dict[str, float | int]] = {}

    for header in headers:
        numeric_values = [value for value in (row.get(header) for row in rows) if isinstance(value, (int, float))]
        if numeric_values:
            numeric_columns[header] = {
                "count": len(numeric_values),
                "sum": float(sum(numeric_values)),
                "min": float(min(numeric_values)),
                "max": float(max(numeric_values)),
            }

    return {
        "columns": len(headers),
        "rows": len(rows),
        "numeric_columns": numeric_columns,
    }
