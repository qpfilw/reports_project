from __future__ import annotations
from typing import Any, Iterable
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.enums import NotificationTypeEnum, ReportStatusEnum
from app.models.notification import Notification
from app.models.processing_task import ProcessingTask
from app.models.project import Project
from app.models.report import Report
from app.models.user import User


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        *,
        user_id: int,
        type: NotificationTypeEnum,
        title: str,
        message: str,
        project_id: int | None = None,
        report_id: int | None = None,
        processing_task_id: int | None = None,
        payload_json: dict[str, Any] | None = None,
        is_read: bool = False,
        flush: bool = True,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            project_id=project_id,
            report_id=report_id,
            processing_task_id=processing_task_id,
            type=type,
            title=title,
            message=message,
            payload_json=payload_json or {},
            is_read=is_read,
        )
        self.db.add(notification)
        if flush:
            self.db.flush()
        return notification

    def create_bulk_notifications(
        self,
        *,
        user_ids: Iterable[int],
        type: NotificationTypeEnum,
        title: str,
        message: str,
        project_id: int | None = None,
        report_id: int | None = None,
        processing_task_id: int | None = None,
        payload_json: dict[str, Any] | None = None,
        flush: bool = True,
    ) -> list[Notification]:
        notifications: list[Notification] = []
        unique_user_ids = self._unique_user_ids(user_ids)
        for user_id in unique_user_ids:
            notifications.append(
                self.create_notification(
                    user_id=user_id,
                    type=type,
                    title=title,
                    message=message,
                    project_id=project_id,
                    report_id=report_id,
                    processing_task_id=processing_task_id,
                    payload_json=payload_json,
                    flush=False,
                )
            )
        if flush and notifications:
            self.db.flush()
        return notifications

    def notify_report_submitted(self, report: Report) -> list[Notification]:
        recipient_ids = self._collect_report_recipient_ids(report)
        return self.create_bulk_notifications(
            user_ids=recipient_ids,
            type=NotificationTypeEnum.REPORT_SUBMITTED,
            title=f"Отчёт отправлен на рассмотрение: {report.title}",
            message=(
                f"Отчёт «{report.title}» переведён в статус "
                f"«{self._humanize_report_status(report.status)}»."
            ),
            project_id=report.project_id,
            report_id=report.id,
            payload_json={
                "report_status": report.status.value if hasattr(report.status, "value") else str(report.status),
                "report_title": report.title,
            },
        )

    def notify_report_status_changed(
        self,
        report: Report,
        *,
        previous_status: ReportStatusEnum | str | None = None,
    ) -> list[Notification]:
        recipient_ids = self._collect_report_recipient_ids(report)
        return self.create_bulk_notifications(
            user_ids=recipient_ids,
            type=NotificationTypeEnum.REPORT_STATUS_CHANGED,
            title=f"Изменён статус отчёта: {report.title}",
            message=(
                f"Статус отчёта «{report.title}» изменён "
                f"с «{self._humanize_report_status(previous_status)}» "
                f"на «{self._humanize_report_status(report.status)}»."
            ),
            project_id=report.project_id,
            report_id=report.id,
            payload_json={
                "previous_status": previous_status.value if hasattr(previous_status, "value") else previous_status,
                "current_status": report.status.value if hasattr(report.status, "value") else str(report.status),
                "report_title": report.title,
            },
        )

    def notify_report_approved(self, report: Report) -> list[Notification]:
        recipient_ids = self._collect_report_recipient_ids(report)
        return self.create_bulk_notifications(
            user_ids=recipient_ids,
            type=NotificationTypeEnum.REPORT_APPROVED,
            title=f"Отчёт утверждён: {report.title}",
            message=f"Отчёт «{report.title}» успешно утверждён.",
            project_id=report.project_id,
            report_id=report.id,
            payload_json={"report_status": ReportStatusEnum.APPROVED.value, "report_title": report.title},
        )

    def notify_report_rejected(self, report: Report) -> list[Notification]:
        recipient_ids = self._collect_report_recipient_ids(report)
        return self.create_bulk_notifications(
            user_ids=recipient_ids,
            type=NotificationTypeEnum.REPORT_REJECTED,
            title=f"Отчёт отклонён: {report.title}",
            message=f"Отчёт «{report.title}» был отклонён и требует доработки.",
            project_id=report.project_id,
            report_id=report.id,
            payload_json={"report_status": ReportStatusEnum.REJECTED.value, "report_title": report.title},
        )

    def notify_task_completed(
        self,
        task: ProcessingTask,
        *,
        message: str | None = None,
    ) -> list[Notification]:
        report = task.report
        recipient_ids = self._collect_task_recipient_ids(task)
        final_message = message or f"Обработка отчёта «{report.title}» завершена успешно."
        return self.create_bulk_notifications(
            user_ids=recipient_ids,
            type=NotificationTypeEnum.TASK_COMPLETED,
            title=f"Обработка завершена: {report.title}",
            message=final_message,
            project_id=report.project_id,
            report_id=report.id,
            processing_task_id=task.id,
            payload_json={
                "task_status": task.status.value if hasattr(task.status, "value") else str(task.status),
                "quality_score": task.quality_score,
                "warning_count": task.warning_count,
                "error_count": task.error_count,
            },
        )

    def notify_task_failed(
        self,
        task: ProcessingTask,
        *,
        message: str | None = None,
    ) -> list[Notification]:
        report = task.report
        recipient_ids = self._collect_task_recipient_ids(task)
        final_message = message or (
            f"Обработка отчёта «{report.title}» завершилась ошибкой: "
            f"{task.error_summary or 'см. журнал обработки'}."
        )
        return self.create_bulk_notifications(
            user_ids=recipient_ids,
            type=NotificationTypeEnum.TASK_FAILED,
            title=f"Ошибка обработки: {report.title}",
            message=final_message,
            project_id=report.project_id,
            report_id=report.id,
            processing_task_id=task.id,
            payload_json={
                "task_status": task.status.value if hasattr(task.status, "value") else str(task.status),
                "error_summary": task.error_summary,
                "warning_count": task.warning_count,
                "error_count": task.error_count,
            },
        )

    def notify_system_alert(
        self,
        *,
        user_ids: Iterable[int],
        title: str,
        message: str,
        payload_json: dict[str, Any] | None = None,
        project_id: int | None = None,
        report_id: int | None = None,
        processing_task_id: int | None = None,
    ) -> list[Notification]:
        return self.create_bulk_notifications(
            user_ids=user_ids,
            type=NotificationTypeEnum.SYSTEM_ALERT,
            title=title,
            message=message,
            project_id=project_id,
            report_id=report_id,
            processing_task_id=processing_task_id,
            payload_json=payload_json,
        )

    def list_unread_for_user(self, user_id: int) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .order_by(Notification.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    @staticmethod
    def _humanize_report_status(status_value: ReportStatusEnum | str | None) -> str:
        if status_value is None:
            return "не определён"
        raw = status_value.value if hasattr(status_value, "value") else str(status_value)
        mapping = {
            "draft": "черновик",
            "uploaded": "файл загружен",
            "processing": "в обработке",
            "processed": "обработан",
            "failed": "обработка завершилась ошибкой",
            "on_review": "на рассмотрении",
            "on_approval": "на утверждении",
            "approved": "утверждён",
            "rejected": "отклонён",
            "rework": "на доработке",
            "archived": "архивирован",
        }
        return mapping.get(raw, raw)

    @staticmethod
    def _unique_user_ids(user_ids: Iterable[int | None]) -> list[int]:
        seen: set[int] = set()
        result: list[int] = []
        for user_id in user_ids:
            if user_id is None:
                continue
            if user_id in seen:
                continue
            seen.add(user_id)
            result.append(user_id)
        return result

    def _collect_report_recipient_ids(self, report: Report) -> list[int]:
        return self._unique_user_ids(
            [
                report.creator_id,
                report.current_assignee_id,
                report.approver_id,
            ]
        )

    def _collect_task_recipient_ids(self, task: ProcessingTask) -> list[int]:
        report = task.report
        return self._unique_user_ids(
            [
                task.created_by,
                report.creator_id if report is not None else None,
                report.current_assignee_id if report is not None else None,
                report.approver_id if report is not None else None,
            ]
        )