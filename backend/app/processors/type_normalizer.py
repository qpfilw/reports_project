from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation


_DATE_PATTERNS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y")


def _normalize_datetime(value: datetime) -> str:
    if (
        value.hour == 0
        and value.minute == 0
        and value.second == 0
        and value.microsecond == 0
    ):
        return value.date().isoformat()
    return value.isoformat(sep=" ", timespec="seconds")


def _normalize_date_string(value: str) -> str | None:
    raw = value.strip()
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw)
        return _normalize_datetime(parsed)
    except ValueError:
        pass

    for pattern in _DATE_PATTERNS:
        try:
            return datetime.strptime(raw, pattern).date().isoformat()
        except ValueError:
            continue

    return None


def _normalize_scalar(value: object) -> object:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, datetime):
        return _normalize_datetime(value)

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None

        lowered = stripped.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"

        normalized_number = stripped.replace(" ", "").replace(",", ".")
        try:
            decimal_value = Decimal(normalized_number)
            if decimal_value == decimal_value.to_integral_value():
                return int(decimal_value)
            return float(decimal_value)
        except InvalidOperation:
            pass

        normalized_date = _normalize_date_string(stripped)
        if normalized_date is not None:
            return normalized_date

        return stripped

    return str(value)


def normalize_row_types(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {column: _normalize_scalar(value) for column, value in row.items()}
        for row in rows
    ]
