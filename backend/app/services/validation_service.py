from __future__ import annotations
from pathlib import Path
from typing import Any
from app.processors.csv_reader import read_csv_rows
from app.processors.rules_engine import analyze_rows
from app.processors.table_cleaner import drop_empty_rows
from app.processors.type_normalizer import normalize_row_types
from app.processors.xlsx_reader import read_xlsx_rows


class ValidationService:
    """
    Централизованный сервис валидации входных данных отчётности.

    Задачи сервиса:
    1. Прочитать исходный файл.
    2. Очистить таблицу от пустых строк.
    3. Нормализовать типы значений.
    4. Выполнить правила валидации через processors.rules_engine.analyze_rows().
    5. Вернуть унифицированный словарь с результатами проверки.
    """

    SUPPORTED_SUFFIXES = {".csv", ".xlsx"}

    def validate_file(self, source_path: str | Path) -> dict[str, Any]:
        source_path = Path(source_path)
        self._ensure_supported_format(source_path)

        raw_rows = self._read_source_rows(source_path)
        return self.validate_rows(raw_rows)

    def validate_rows(self, raw_rows: list[dict[str, Any]]) -> dict[str, Any]:
        cleaned_rows = drop_empty_rows(raw_rows)
        normalized_rows = normalize_row_types(cleaned_rows)

        analysis = analyze_rows(normalized_rows)

        warnings = list(analysis.get("warnings") or [])
        errors = list(analysis.get("errors") or [])
        has_fatal_errors = bool(analysis.get("has_fatal_errors", False))

        rows_count = len(normalized_rows)
        missing_required_count = int(analysis.get("missing_required_count", 0))
        invalid_numeric_count = int(analysis.get("invalid_numeric_count", 0))
        invalid_date_count = int(analysis.get("invalid_date_count", 0))
        duplicate_rows_count = int(analysis.get("duplicate_rows_count", 0))
        fatal_errors_count = int(analysis.get("fatal_errors_count", 0))

        quality_score = self.calculate_quality_score(
            rows_count=rows_count,
            warnings_count=len(warnings),
            errors_count=len(errors),
            missing_required_count=missing_required_count,
            invalid_numeric_count=invalid_numeric_count,
            invalid_date_count=invalid_date_count,
            duplicate_rows_count=duplicate_rows_count,
            fatal_errors_count=fatal_errors_count,
        )

        return {
            "raw_rows": raw_rows,
            "cleaned_rows": cleaned_rows,
            "normalized_rows": normalized_rows,
            "rows_count": rows_count,
            "warnings": warnings,
            "errors": errors,
            "has_fatal_errors": has_fatal_errors,
            "warnings_count": len(warnings),
            "errors_count": len(errors),
            "missing_required_count": missing_required_count,
            "invalid_numeric_count": invalid_numeric_count,
            "invalid_date_count": invalid_date_count,
            "duplicate_rows_count": duplicate_rows_count,
            "fatal_errors_count": fatal_errors_count,
            "quality_score": quality_score,
        }

    def validate_headers(
        self,
        headers: list[str],
        *,
        required_headers: list[str] | None = None,
    ) -> dict[str, Any]:
        normalized_headers = [str(header).strip() for header in headers if str(header).strip()]
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        if not normalized_headers:
            errors.append(
                self._build_issue(
                    level="error",
                    error_code="EMPTY_HEADERS",
                    error_type="structure",
                    details="Входной файл не содержит заголовков колонок.",
                    is_critical=True,
                )
            )

        if required_headers:
            missing_headers = [header for header in required_headers if header not in normalized_headers]
            for header in missing_headers:
                errors.append(
                    self._build_issue(
                        level="error",
                        error_code="MISSING_REQUIRED_HEADER",
                        error_type="structure",
                        details=f"Отсутствует обязательная колонка '{header}'.",
                        field_path=header,
                        is_critical=True,
                    )
                )

        duplicates = self._find_duplicates(normalized_headers)
        for header in duplicates:
            warnings.append(
                self._build_issue(
                    level="warning",
                    error_code="DUPLICATE_HEADER",
                    error_type="structure",
                    details=f"Обнаружен повторяющийся заголовок '{header}'.",
                    field_path=header,
                    is_critical=False,
                )
            )

        return {
            "headers": normalized_headers,
            "warnings": warnings,
            "errors": errors,
            "has_fatal_errors": any(item.get("is_critical") for item in errors),
        }

    @staticmethod
    def calculate_quality_score(
        *,
        rows_count: int,
        warnings_count: int,
        errors_count: int,
        missing_required_count: int,
        invalid_numeric_count: int,
        invalid_date_count: int,
        duplicate_rows_count: int,
        fatal_errors_count: int,
    ) -> float:
        if rows_count == 0:
            return 0.0

        penalty = 0.0
        penalty += warnings_count * 0.01
        penalty += errors_count * 0.08
        penalty += missing_required_count * 0.02
        penalty += invalid_numeric_count * 0.02
        penalty += invalid_date_count * 0.02
        penalty += duplicate_rows_count * 0.03
        penalty += fatal_errors_count * 0.15

        return round(max(0.0, min(1.0, 1.0 - penalty)), 4)

    def _read_source_rows(self, source_path: Path) -> list[dict[str, Any]]:
        suffix = source_path.suffix.lower()
        if suffix == ".csv":
            return read_csv_rows(source_path)
        if suffix == ".xlsx":
            return read_xlsx_rows(source_path)
        raise ValueError("Unsupported file format for validation.")

    def _ensure_supported_format(self, source_path: Path) -> None:
        suffix = source_path.suffix.lower()
        if suffix not in self.SUPPORTED_SUFFIXES:
            raise ValueError("Unsupported file format for validation.")

    @staticmethod
    def _find_duplicates(values: list[str]) -> list[str]:
        seen: set[str] = set()
        duplicates: list[str] = []
        for value in values:
            if value in seen and value not in duplicates:
                duplicates.append(value)
            seen.add(value)
        return duplicates

    @staticmethod
    def _build_issue(
        *,
        level: str,
        error_code: str,
        error_type: str,
        details: str,
        field_path: str | None = None,
        row_number: int | None = None,
        source_value: str | None = None,
        is_critical: bool = False,
    ) -> dict[str, Any]:
        return {
            "level": level,
            "error_code": error_code,
            "error_type": error_type,
            "details": details,
            "field_path": field_path,
            "row_number": row_number,
            "source_value": source_value,
            "is_critical": is_critical,
        }