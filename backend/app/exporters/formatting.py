from __future__ import annotations
from datetime import date, datetime
_DATE_OUTPUT_FORMAT = "%d.%m.%Y"

def _parse_iso_date_like(value: str) -> date | None:
    raw = value.strip()
    if not raw:
        return None

    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass

    try:
        parsed = datetime.fromisoformat(raw)
        return parsed.date()
    except ValueError:
        return None

def format_export_value(value: object) -> object:
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime(_DATE_OUTPUT_FORMAT)

    if isinstance(value, date):
        return value.strftime(_DATE_OUTPUT_FORMAT)

    if isinstance(value, str):
        parsed = _parse_iso_date_like(value)
        if parsed is not None:
            return parsed.strftime(_DATE_OUTPUT_FORMAT)
        return value

    return value

def format_export_text(value: object) -> str:
    formatted = format_export_value(value)
    return "" if formatted is None else str(formatted)

def excel_cell_value_and_format(value: object) -> tuple[object, str | None]:
    if value is None:
        return "", None

    if isinstance(value, datetime):
        return value.date(), "DD.MM.YYYY"

    if isinstance(value, date):
        return value, "DD.MM.YYYY"

    if isinstance(value, str):
        parsed = _parse_iso_date_like(value)
        if parsed is not None:
            return parsed, "DD.MM.YYYY"
        return value, None

    return value, None
