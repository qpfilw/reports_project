from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.exporters.csv_exporter import export_rows_to_csv
from app.exporters.pdf_exporter import export_processing_summary_to_pdf
from app.exporters.xlsx_exporter import export_rows_to_xlsx
from app.models.export_artifact import ExportArtifact
from app.models.normalized_dataset import NormalizedDataset
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.models.user import User
from app.utils.file_hash import sha256_for_file
from app.utils.storage import build_export_relative_path, read_json, resolve_storage_path


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_processing_result(
        self,
        *,
        processing_task_id: int,
        export_format: str,
        created_by: User | None,
    ) -> ExportArtifact:
        format_value = getattr(export_format, "value", export_format)
        task = self.db.get(ProcessingTask, processing_task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

        task_status = getattr(task.status, "value", task.status)
        if task_status != "success":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Export is available only for successfully processed tasks.",
            )

        if task.normalized_dataset is None:
            dataset = self.db.query(NormalizedDataset).filter_by(processing_task_id=task.id).one_or_none()
        else:
            dataset = task.normalized_dataset

        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing task has no normalized dataset yet.",
            )

        payload = read_json(dataset.data_location)
        rows = list(payload.get("rows", []))
        summary = dict(payload.get("summary_json", {}))
        preview_rows = list(payload.get("preview_json", []))

        relative_path = build_export_relative_path(
            report_id=task.report_id,
            task_id=task.id,
            extension=str(format_value),
        )
        absolute_path = resolve_storage_path(relative_path)

        if format_value == "csv":
            export_rows_to_csv(absolute_path, rows)
        elif format_value == "xlsx":
            export_rows_to_xlsx(absolute_path, rows)
        elif format_value == "pdf":
            report = self.db.get(Report, task.report_id)
            export_processing_summary_to_pdf(
                absolute_path,
                report_title=report.title if report is not None else f"Report {task.report_id}",
                task_id=task.id,
                summary=summary,
                preview_rows=preview_rows,
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported export format.")

        artifact = ExportArtifact(
            processing_task_id=task.id,
            report_id=task.report_id,
            format=format_value,
            storage_path=relative_path,
            file_size=absolute_path.stat().st_size,
            checksum_sha256=sha256_for_file(absolute_path),
            created_by=created_by.id if created_by is not None else None,
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact
