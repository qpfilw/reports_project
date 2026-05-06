from __future__ import annotations

from collections import Counter
from datetime import date, datetime


MANDATORY_COLUMN_HINTS = (
    "id",
    "сумм",
    "дата",
    "date",
    "name",
    "amount",
    "count",
    "кол",
)

NUMERIC_COLUMN_HINTS = (
    "id",
    "sum",
    "amount",
    "сумм",
    "итог",
    "count",
    "qty",
    "кол",
    "number",
    "номер",
    "цена",
    "price",
    "ндс",
    "vat",
    "лимит",
    "план",
    "отклон",
    "коэффициент",
)

DATE_COLUMN_HINTS = (
    "date",
    "дата",
    "period",
    "период",
)

# Колонки, которые похожи на числовые по слову "код", но на практике являются строковыми справочными ключами.
TEXT_CODE_COLUMN_HINTS = (
    "код статьи",
    "код категории",
    "код контрагента",
    "код номенклатуры",
    "код товара",
    "код услуги",
    "артикул",
    "sku",
    "article",
)


def _normalize_header(header: str) -> str:
    return " ".join(str(header).lower().strip().split())


def _is_numeric_column(header: str) -> bool:
    header_lower = _normalize_header(header)

    if any(token in header_lower for token in TEXT_CODE_COLUMN_HINTS):
        return False

    return any(token in header_lower for token in NUMERIC_COLUMN_HINTS)


def _is_date_column(header: str) -> bool:
    header_lower = _normalize_header(header)
    return any(token in header_lower for token in DATE_COLUMN_HINTS)


def _is_valid_date_value(value: object) -> bool:
    if isinstance(value, (date, datetime)):
        return True
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return False
        try:
            date.fromisoformat(raw[:10])
            return True
        except ValueError:
            return False
    return False


def _build_issue(
    *,
    error_code: str,
    error_type: str,
    details: str,
    field_path: str | None = None,
    row_number: int | None = None,
    source_value: str | None = None,
    is_critical: bool = False,
) -> dict[str, object]:
    return {
        "error_code": error_code,
        "error_type": error_type,
        "field_path": field_path,
        "row_number": row_number,
        "source_value": source_value,
        "details": details,
        "is_critical": is_critical,
    }


def analyze_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    warnings: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []

    if not rows:
        errors.append(
            _build_issue(
                error_code="EMPTY_DATASET",
                error_type="dataset",
                details="После чтения файла не найдено ни одной строки данных.",
                is_critical=True,
            )
        )
        return {
            "warnings": warnings,
            "errors": errors,
            "missing_required_count": 0,
            "invalid_numeric_count": 0,
            "invalid_date_count": 0,
            "duplicate_rows_count": 0,
            "fatal_errors_count": 1,
            "has_fatal_errors": True,
        }

    headers = list(rows[0].keys())
    required_headers = [
        header
        for header in headers
        if any(hint in _normalize_header(header) for hint in MANDATORY_COLUMN_HINTS)
    ]

    missing_required_count = 0
    invalid_numeric_count = 0
    invalid_date_count = 0

    row_signatures: list[tuple[tuple[str, object], ...]] = []

    for row_index, row in enumerate(rows, start=2):
        for header in required_headers:
            if row.get(header) in {None, ""}:
                missing_required_count += 1
                errors.append(
                    _build_issue(
                        error_code="MISSING_REQUIRED_VALUE",
                        error_type="validation",
                        field_path=header,
                        row_number=row_index,
                        source_value=None,
                        details=f"Обязательное поле '{header}' не заполнено.",
                        is_critical=True,
                    )
                )

        for header, value in row.items():
            if _is_numeric_column(header):
                if value in {None, ""}:
                    continue
                if not isinstance(value, (int, float)):
                    invalid_numeric_count += 1
                    errors.append(
                        _build_issue(
                            error_code="INVALID_NUMERIC_VALUE",
                            error_type="validation",
                            field_path=header,
                            row_number=row_index,
                            source_value=str(value),
                            details=f"Поле '{header}' содержит нечисловое значение.",
                            is_critical=True,
                        )
                    )

            if _is_date_column(header):
                if value in {None, ""}:
                    continue
                if not _is_valid_date_value(value):
                    invalid_date_count += 1
                    errors.append(
                        _build_issue(
                            error_code="INVALID_DATE_VALUE",
                            error_type="validation",
                            field_path=header,
                            row_number=row_index,
                            source_value=str(value),
                            details=f"Поле '{header}' содержит некорректную дату.",
                            is_critical=True,
                        )
                    )

        row_signatures.append(tuple(sorted(row.items())))

    duplicates_counter = Counter(row_signatures)
    duplicate_rows_count = sum(count - 1 for count in duplicates_counter.values() if count > 1)
    if duplicate_rows_count:
        warnings.append(
            _build_issue(
                error_code="DUPLICATE_ROWS",
                error_type="dataset",
                details=f"Обнаружено повторяющихся строк: {duplicate_rows_count}.",
                is_critical=False,
            )
        )

    fatal_errors_count = sum(1 for issue in errors if bool(issue.get("is_critical", False)))

    return {
        "warnings": warnings,
        "errors": errors,
        "missing_required_count": missing_required_count,
        "invalid_numeric_count": invalid_numeric_count,
        "invalid_date_count": invalid_date_count,
        "duplicate_rows_count": duplicate_rows_count,
        "fatal_errors_count": fatal_errors_count,
        "has_fatal_errors": fatal_errors_count > 0,
    }
