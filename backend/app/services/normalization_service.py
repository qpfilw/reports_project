from __future__ import annotations

from pathlib import Path

from app.processors.aggregation import build_aggregation
from app.processors.script_runner import ScriptExecutionError, ScriptRunResult, ScriptSecurityError, run_processing_script
from app.processors.result_builder import build_preview, build_schema, build_summary
from app.services.validation_service import ValidationService
from app.utils.storage import build_normalized_relative_path, write_json


class NormalizationService:
    def __init__(self) -> None:
        self.validation_service = ValidationService()

    def normalize_file(
        self,
        *,
        source_path: str | Path,
        report_id: int,
        task_id: int,
        processing_script_code: str | None = None,
        processing_script_name: str | None = None,
        processing_script_context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        source_path = Path(source_path)

        validation_result = self.validation_service.validate_file(source_path)
        normalized_rows = list(validation_result["normalized_rows"])
        warnings = list(validation_result["warnings"])
        errors = list(validation_result["errors"])
        has_fatal_errors = bool(validation_result["has_fatal_errors"])
        script_result: ScriptRunResult | None = None

        if processing_script_code and normalized_rows and not has_fatal_errors:
            try:
                script_result = run_processing_script(
                    rows=normalized_rows,
                    script_code=processing_script_code,
                    context=processing_script_context,
                    timeout_seconds=int((processing_script_context or {}).get("timeout_seconds") or 120),
                )
                normalized_rows = script_result.rows
                warnings.extend(script_result.warnings)
            except (ScriptExecutionError, ScriptSecurityError) as exc:
                errors.append(
                    {
                        "error_type": "processing_script",
                        "error_code": "PROCESSING_SCRIPT_FAILED",
                        "details": str(exc),
                        "field_path": None,
                        "row_number": None,
                        "source_value": None,
                        "is_critical": True,
                    }
                )
                has_fatal_errors = True

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
        if script_result is not None:
            summary_json["script_processing"] = {
                "script_name": processing_script_name,
                "mode": "advanced",
                "added_columns": script_result.added_columns,
                "added_columns_count": len(script_result.added_columns),
                "processed_rows": script_result.stats.get("processed_rows", len(normalized_rows)),
                "script_stats": script_result.stats,
                "script_summary": script_result.summary,
            }
            summary_json["control_summary"] = _build_control_summary(normalized_rows)
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
            "rows_count": len(normalized_rows),
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

def _build_control_summary(rows: list[dict[str, object]]) -> dict[str, int]:
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    requires_approval = 0
    requires_control = 0
    requires_reconciliation = 0

    for row in rows:
        risk = str(row.get("Уровень риска") or row.get("risk_level") or "").strip().lower()
        if risk in {"низкий", "low"}:
            risk_counts["low"] += 1
        elif risk in {"средний", "medium"}:
            risk_counts["medium"] += 1
        elif risk in {"высокий", "high"}:
            risk_counts["high"] += 1

        approval = str(row.get("Требуется согласование") or row.get("requires_approval") or "").strip().lower()
        if approval in {"да", "true", "1", "yes"}:
            requires_approval += 1

        control = str(row.get("Результат контроля") or row.get("control_result") or "").strip().lower()
        if "контрол" in control:
            requires_control += 1
        if "сверк" in control:
            requires_reconciliation += 1

    return {
        "risk_low": risk_counts["low"],
        "risk_medium": risk_counts["medium"],
        "risk_high": risk_counts["high"],
        "requires_approval": requires_approval,
        "requires_control": requires_control,
        "requires_payment_reconciliation": requires_reconciliation,
    }
