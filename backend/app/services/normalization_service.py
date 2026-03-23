from __future__ import annotations

from pathlib import Path

from app.processors.aggregation import build_aggregation
from app.processors.csv_reader import read_csv_rows
from app.processors.result_builder import build_preview, build_schema, build_summary
from app.processors.rules_engine import analyze_rows
from app.processors.table_cleaner import drop_empty_rows
from app.processors.type_normalizer import normalize_row_types
from app.processors.xlsx_reader import read_xlsx_rows
from app.utils.storage import build_normalized_relative_path, write_json


class NormalizationService:
    def normalize_file(self, *, source_path: str | Path, report_id: int, task_id: int) -> dict[str, object]:
        source_path = Path(source_path)
        suffix = source_path.suffix.lower()

        if suffix == ".csv":
            raw_rows = read_csv_rows(source_path)
        elif suffix == ".xlsx":
            raw_rows = read_xlsx_rows(source_path)
        else:
            raise ValueError("Unsupported file format for normalization.")

        cleaned_rows = drop_empty_rows(raw_rows)
        normalized_rows = normalize_row_types(cleaned_rows)
        analysis = analyze_rows(normalized_rows)
        warnings = list(analysis["warnings"])
        errors = list(analysis["errors"])
        has_fatal_errors = bool(analysis["has_fatal_errors"])

        aggregation = build_aggregation(normalized_rows) if normalized_rows else {"rows": 0, "columns": 0, "numeric_columns": {}}
        schema_json = build_schema(normalized_rows)
        summary_json = build_summary(
            normalized_rows,
            warnings_count=len(warnings),
            errors_count=len(errors),
            aggregation=aggregation,
        )
        preview_json = build_preview(normalized_rows)

        quality_score = self._calculate_quality_score(
            rows_count=len(normalized_rows),
            warnings_count=len(warnings),
            errors_count=len(errors),
            missing_required_count=int(analysis["missing_required_count"]),
            invalid_numeric_count=int(analysis["invalid_numeric_count"]),
            invalid_date_count=int(analysis["invalid_date_count"]),
            duplicate_rows_count=int(analysis["duplicate_rows_count"]),
            fatal_errors_count=int(analysis["fatal_errors_count"]),
        )

        data_location: str | None = None
        if not has_fatal_errors and not errors:
            data_location = build_normalized_relative_path(report_id=report_id, task_id=task_id)
            write_json(
                data_location,
                {
                    "rows": normalized_rows,
                    "schema_json": schema_json,
                    "summary_json": summary_json,
                    "preview_json": preview_json,
                    "warnings": warnings,
                    "errors": errors,
                },
            )

        return {
            "rows_count": len(normalized_rows),
            "schema_json": schema_json,
            "summary_json": summary_json,
            "preview_json": preview_json,
            "data_location": data_location,
            "warnings": warnings,
            "errors": errors,
            "has_fatal_errors": has_fatal_errors,
            "fatal_errors_count": int(analysis["fatal_errors_count"]),
            "quality_score": quality_score,
        }

    @staticmethod
    def _calculate_quality_score(
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