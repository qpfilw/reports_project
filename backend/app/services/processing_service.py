from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import ProcessingLogLevelEnum, ProcessingStatusEnum
from app.models.normalized_dataset import NormalizedDataset
from app.models.processing_log import ProcessingLog
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.models.report_upload import ReportUpload
from app.models.task_error import TaskError
from app.models.user import User
from app.services.normalization_service import NormalizationService
from app.utils.storage import resolve_storage_path


class ProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.normalization_service = NormalizationService()

    def launch_processing_task(
        self,
        *,
        report_id: int,
        report_upload_id: int,
        ml_template_id: int | None,
        created_by: User | None,
        priority: int,
        params_json: dict[str, object] | None = None,
    ) -> ProcessingTask:
        report = self.db.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

        upload = self.db.get(ReportUpload, report_upload_id)
        if upload is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report upload not found.")

        if upload.report_id != report_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload does not belong to the specified report.",
            )

        task = ProcessingTask(
            report_id=report_id,
            report_upload_id=report_upload_id,
            ml_template_id=ml_template_id,
            created_by=created_by.id if created_by is not None else None,
            priority=priority,
            params_json=params_json or {},
            status=ProcessingStatusEnum.QUEUED,
            progress=0,
            warning_count=0,
            error_count=0,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        self.append_log(
            task=task,
            level=ProcessingLogLevelEnum.INFO,
            stage="queue",
            message="Задача поставлена в очередь на обработку.",
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    def dispatch_processing_task(self, *, task_id: int) -> ProcessingTask:
        return self.run_processing_task_sync(task_id=task_id)

    def run_processing_task_sync(self, *, task_id: int) -> ProcessingTask:
        task = self.db.get(ProcessingTask, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

        upload = self.db.get(ReportUpload, task.report_upload_id)
        if upload is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report upload not found.")

        self._mark_task_running(task)
        self.append_log(
            task=task,
            level=ProcessingLogLevelEnum.INFO,
            stage="read",
            message="Запущено чтение и нормализация файла.",
            context_json={"storage_path": upload.storage_path},
        )

        try:
            normalization_result = self.normalization_service.normalize_file(
                source_path=resolve_storage_path(upload.storage_path),
                report_id=task.report_id,
                task_id=task.id,
            )
            self._store_warnings_and_errors(task=task, normalization_result=normalization_result)
            self._apply_validation_statistics(task=task, normalization_result=normalization_result)

            if self._has_validation_errors(normalization_result):
                self._delete_normalized_dataset(task)
                self._mark_task_failed(
                    task=task,
                    error_summary=self._build_validation_error_summary(normalization_result),
                    normalization_result=normalization_result,
                )
            else:
                self._store_normalized_dataset(task=task, normalization_result=normalization_result)
                self._mark_task_success(task=task, normalization_result=normalization_result)
        except Exception as exc:
            self.append_error(
                task=task,
                error_code="PROCESSING_FAILED",
                error_type="runtime",
                details=str(exc),
                is_critical=True,
            )
            self._mark_task_failed(task=task, error_summary=str(exc))
        self.db.commit()
        self.db.refresh(task)
        return task

    def append_log(
        self,
        *,
        task: ProcessingTask,
        level: ProcessingLogLevelEnum,
        stage: str,
        message: str,
        context_json: dict[str, object] | None = None,
    ) -> ProcessingLog:
        log = ProcessingLog(
            processing_task_id=task.id,
            level=level,
            stage=stage,
            message=message,
            context_json=context_json or {},
        )
        self.db.add(log)
        self.db.flush()
        return log

    def append_error(
        self,
        *,
        task: ProcessingTask,
        error_code: str,
        error_type: str,
        details: str | None,
        field_path: str | None = None,
        row_number: int | None = None,
        source_value: str | None = None,
        is_critical: bool = False,
    ) -> TaskError:
        error = TaskError(
            processing_task_id=task.id,
            error_code=error_code,
            error_type=error_type,
            field_path=field_path,
            row_number=row_number,
            source_value=source_value,
            details=details,
            is_critical=is_critical,
        )
        self.db.add(error)
        if is_critical and not task.error_summary:
            task.error_summary = details or error_code
        self.db.flush()
        return error

    def _mark_task_running(self, task: ProcessingTask) -> None:
        task.status = ProcessingStatusEnum.RUNNING
        task.progress = 10
        task.started_at = datetime.now(timezone.utc)
        task.finished_at = None
        task.error_summary = None
        self.db.flush()

    def _mark_task_success(self, *, task: ProcessingTask, normalization_result: dict[str, object]) -> None:
        task.status = ProcessingStatusEnum.SUCCESS
        task.progress = 100
        task.finished_at = datetime.now(timezone.utc)
        self.append_log(
            task=task,
            level=ProcessingLogLevelEnum.INFO,
            stage="complete",
            message="Обработка файла успешно завершена.",
            context_json={
                "rows_count": normalization_result["rows_count"],
                "quality_score": normalization_result["quality_score"],
                "warnings_count": len(list(normalization_result["warnings"])),
                "errors_count": len(list(normalization_result["errors"])),
            },
        )
        self.db.flush()

    def _mark_task_failed(
        self,
        *,
        task: ProcessingTask,
        error_summary: str,
        normalization_result: dict[str, object] | None = None,
    ) -> None:
        task.status = ProcessingStatusEnum.FAILED
        task.progress = 100
        task.finished_at = datetime.now(timezone.utc)
        task.error_summary = error_summary
        if normalization_result is not None:
            task.quality_score = float(normalization_result["quality_score"])
            task.warning_count = len(list(normalization_result["warnings"]))
            task.error_count = len(list(normalization_result["errors"]))
        else:
            task.error_count = max(task.error_count or 0, 1)
        self.append_log(
            task=task,
            level=ProcessingLogLevelEnum.ERROR,
            stage="failed",
            message="Обработка файла завершилась ошибкой.",
            context_json={
                "error_summary": error_summary,
                "warnings_count": task.warning_count,
                "errors_count": task.error_count,
            },
        )
        self.db.flush()

    def _store_normalized_dataset(self, *, task: ProcessingTask, normalization_result: dict[str, object]) -> None:
        dataset = task.normalized_dataset
        if dataset is None:
            dataset = NormalizedDataset(
                processing_task_id=task.id,
                report_id=task.report_id,
            )
            self.db.add(dataset)

        dataset.rows_count = int(normalization_result["rows_count"])
        dataset.schema_json = dict(normalization_result["schema_json"])
        dataset.summary_json = dict(normalization_result["summary_json"])
        dataset.preview_json = list(normalization_result["preview_json"])
        dataset.data_location = str(normalization_result["data_location"])
        task.progress = 85
        self.db.flush()

    def _store_warnings_and_errors(self, *, task: ProcessingTask, normalization_result: dict[str, object]) -> None:
        for warning in normalization_result["warnings"]:
            self.append_error(
                task=task,
                error_code=str(warning["error_code"]),
                error_type=str(warning["error_type"]),
                details=str(warning.get("details") or ""),
                field_path=warning.get("field_path"),
                row_number=warning.get("row_number"),
                source_value=warning.get("source_value"),
                is_critical=bool(warning.get("is_critical", False)),
            )

        for error in normalization_result["errors"]:
            self.append_error(
                task=task,
                error_code=str(error["error_code"]),
                error_type=str(error["error_type"]),
                details=str(error.get("details") or ""),
                field_path=error.get("field_path"),
                row_number=error.get("row_number"),
                source_value=error.get("source_value"),
                is_critical=bool(error.get("is_critical", False)),
            )

    def _apply_validation_statistics(self, *, task: ProcessingTask, normalization_result: dict[str, object]) -> None:
        task.quality_score = float(normalization_result["quality_score"])
        task.warning_count = len(list(normalization_result["warnings"]))
        task.error_count = len(list(normalization_result["errors"]))
        self.db.flush()

    @staticmethod
    def _has_validation_errors(normalization_result: dict[str, object]) -> bool:
        return bool(normalization_result.get("has_fatal_errors")) or bool(normalization_result.get("errors"))

    @staticmethod
    def _build_validation_error_summary(normalization_result: dict[str, object]) -> str:
        errors = list(normalization_result.get("errors") or [])
        if not errors:
            return "Обработка остановлена из-за ошибок валидации входных данных."

        first_error = errors[0]
        details = str(first_error.get("details") or "")
        total_errors = len(errors)
        if total_errors == 1:
            return details or "Обработка остановлена из-за ошибки валидации входных данных."
        return f"{details} Всего ошибок валидации: {total_errors}."

    def _delete_normalized_dataset(self, task: ProcessingTask) -> None:
        dataset = task.normalized_dataset
        if dataset is not None:
            self.db.delete(dataset)
            self.db.flush()
