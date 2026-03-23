from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.inference.map_columns import map_columns
from app.ml.inference.predict_template import predict_template
from app.models.ml_template import MlTemplate
from app.models.processing_task import ProcessingTask
from app.models.report_upload import ReportUpload
from app.processors.csv_reader import read_csv_rows
from app.processors.xlsx_reader import read_xlsx_rows
from app.utils.storage import resolve_storage_path


class MLService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_templates(self, *, report_type_id: int | None) -> list[MlTemplate]:
        stmt = select(MlTemplate).where(MlTemplate.is_active.is_(True))
        if report_type_id is not None:
            stmt = stmt.where(MlTemplate.target_report_type_id == report_type_id)
        stmt = stmt.order_by(MlTemplate.is_default.desc(), MlTemplate.id.asc())
        return list(self.db.scalars(stmt).all())

    def extract_headers_from_storage(self, *, storage_path: str) -> list[str]:
        return self.extract_headers_from_path(resolve_storage_path(storage_path))

    def extract_headers_from_path(self, path: str | Path) -> list[str]:
        file_path = Path(path)
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            rows = read_csv_rows(file_path)
        elif suffix == ".xlsx":
            rows = read_xlsx_rows(file_path)
        else:
            return []

        if not rows:
            return []
        return [str(header) for header in rows[0].keys()]

    def build_prediction_payload(
        self,
        *,
        headers: list[str],
        report_type_id: int | None,
        forced_template_id: int | None = None,
    ) -> dict[str, Any]:
        templates = self.get_active_templates(report_type_id=report_type_id)
        prediction = predict_template(headers, templates)
        best_candidate = prediction.get("best")
        auto_apply_threshold = float(prediction.get("auto_apply_threshold", 0.88))

        selected_template: MlTemplate | None = None
        selection_mode = "none"
        if forced_template_id is not None:
            selected_template = self.db.get(MlTemplate, forced_template_id)
            selection_mode = "forced"
        elif best_candidate is not None:
            best_template = best_candidate["template"]
            best_confidence = float(best_candidate["confidence"])
            if best_confidence >= auto_apply_threshold:
                selected_template = best_template
                selection_mode = "auto"
            else:
                selected_template = best_template
                selection_mode = "suggested"

        mapping = map_columns(headers, selected_template)

        return {
            "headers": headers,
            "selection_mode": selection_mode,
            "selected_template": selected_template,
            "prediction": prediction,
            "mapping": mapping,
            "mapping_confirmation_required": bool(mapping["requires_confirmation"] or selection_mode == "suggested"),
        }

    def analyze_upload(
        self,
        *,
        upload: ReportUpload,
        forced_template_id: int | None = None,
    ) -> dict[str, Any]:
        headers = self.extract_headers_from_storage(storage_path=upload.storage_path)
        return self.build_prediction_payload(
            headers=headers,
            report_type_id=upload.report_type_id,
            forced_template_id=forced_template_id,
        )

    def apply_prediction_to_task(
        self,
        *,
        task: ProcessingTask,
        upload: ReportUpload,
        forced_template_id: int | None = None,
    ) -> dict[str, Any]:
        payload = self.analyze_upload(upload=upload, forced_template_id=forced_template_id)
        selected_template = payload["selected_template"]
        prediction = payload["prediction"]
        mapping = payload["mapping"]

        params = dict(task.params_json or {})
        params["headers"] = list(payload["headers"])
        params["prediction_candidates"] = [
            {
                "template_id": item["template"].id,
                "template_code": item["template"].code,
                "confidence": float(item["confidence"]),
                "coverage": float(item["coverage"]),
                "matched_fields": item["matched_fields"],
                "unmatched_fields": item["unmatched_fields"],
            }
            for item in prediction["candidates"]
        ]
        params["ml_prediction"] = {
            "selection_mode": payload["selection_mode"],
            "auto_apply_threshold": float(prediction.get("auto_apply_threshold", 0.88)),
            "mapping_confirmation_required": bool(payload["mapping_confirmation_required"]),
        }
        if prediction.get("best") is not None:
            best = prediction["best"]
            params["ml_prediction"]["best_match"] = {
                "template_id": best["template"].id,
                "template_code": best["template"].code,
                "confidence": float(best["confidence"]),
                "coverage": float(best["coverage"]),
            }
        params["column_matches"] = list(mapping["matches"])
        params["unmatched_headers"] = list(mapping["unmatched_headers"])
        params["mapping_confirmation_required"] = bool(payload["mapping_confirmation_required"])
        task.params_json = params

        if selected_template is not None:
            task.ml_template_id = selected_template.id
            if task.report.ml_template_id is None or payload["selection_mode"] in {"forced", "auto"}:
                task.report.ml_template_id = selected_template.id

        self.db.flush()
        return payload