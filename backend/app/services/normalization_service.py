from __future__ import annotations

from pathlib import Path

from app.processors.aggregation import build_aggregation
from app.processors.result_builder import build_preview, build_schema, build_summary
from app.services.validation_service import ValidationService
from app.utils.storage import build_normalized_relative_path, write_json


class NormalizationService:
    def __init__(self) -> None:
        self.validation_service = ValidationService()

    def normalize_file(self, *, source_path: str | Path, report_id: int, task_id: int) -> dict[str, object]:
        source_path = Path(source_path)

        validation_result = self.validation_service.validate_file(source_path)
        normalized_rows = list(validation_result["normalized_rows"])
        warnings = list(validation_result["warnings"])
        errors = list(validation_result["errors"])
        has_fatal_errors = bool(validation_result["has_fatal_errors"])

        aggregation = (
            build_aggregation(normalized_rows)
            if normalized_rows
            else {"rows": 0, "columns": 0, "numeric_columns": {}}
        )

        schema_json = build_schema(normalized_rows)
        summary_json = build_summary(
            normalized_rows,
            warnings_count=len(warnings),
            errors_count=len(errors),
            aggregation=aggregation,
        )
        preview_json = build_preview(normalized_rows)

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
            "rows_count": int(validation_result["rows_count"]),
            "schema_json": schema_json,
            "summary_json": summary_json,
            "preview_json": preview_json,
            "data_location": data_location,
            "warnings": warnings,
            "errors": errors,
            "has_fatal_errors": has_fatal_errors,
            "fatal_errors_count": int(validation_result["fatal_errors_count"]),
            "quality_score": float(validation_result["quality_score"]),
            "missing_required_count": int(validation_result["missing_required_count"]),
            "invalid_numeric_count": int(validation_result["invalid_numeric_count"]),
            "invalid_date_count": int(validation_result["invalid_date_count"]),
            "duplicate_rows_count": int(validation_result["duplicate_rows_count"]),
        }