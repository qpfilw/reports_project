from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import ReportStatusEnum
from app.models.report import Report


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def mark_uploaded(self, report: Report, *, upload_version: int | None = None, comment: str | None = None) -> Report:
        self._ensure_status(
            report,
            {
                ReportStatusEnum.DRAFT,
                ReportStatusEnum.UPLOADED,
                ReportStatusEnum.PROCESSED,
                ReportStatusEnum.FAILED,
                ReportStatusEnum.REWORK,
                ReportStatusEnum.REJECTED,
            },
            "upload a new file for",
        )
        report.status = ReportStatusEnum.UPLOADED
        if upload_version is not None:
            report.version = max(int(report.version or 1), int(upload_version))
        if comment:
            report.last_comment = comment
        report.submitted_at = None
        report.approved_at = None
        report.rejected_at = None
        self.db.flush()
        return report

    def mark_processing(self, report: Report) -> Report:
        self._ensure_status(
            report,
            {ReportStatusEnum.DRAFT, ReportStatusEnum.UPLOADED, ReportStatusEnum.FAILED, ReportStatusEnum.REWORK},
            "start processing",
        )
        report.status = ReportStatusEnum.PROCESSING
        self.db.flush()
        return report

    def mark_processed(self, report: Report) -> Report:
        report.status = ReportStatusEnum.PROCESSED
        self.db.flush()
        return report

    def mark_failed(self, report: Report, *, error_summary: str | None = None) -> Report:
        report.status = ReportStatusEnum.FAILED
        if error_summary:
            report.last_comment = error_summary
        self.db.flush()
        return report

    def submit_for_review(
        self,
        report: Report,
        *,
        comment: str | None = None,
        current_assignee_id: int | None = None,
    ) -> Report:
        self._ensure_status(report, {ReportStatusEnum.PROCESSED, ReportStatusEnum.REWORK}, "submit for review")
        report.status = ReportStatusEnum.ON_REVIEW
        report.submitted_at = datetime.now(timezone.utc)
        if current_assignee_id is not None:
            report.current_assignee_id = current_assignee_id
        if comment:
            report.last_comment = comment
        self.db.flush()
        return report

    def submit_for_approval(
        self,
        report: Report,
        *,
        comment: str | None = None,
        approver_id: int | None = None,
    ) -> Report:
        self._ensure_status(report, {ReportStatusEnum.ON_REVIEW, ReportStatusEnum.PROCESSED}, "submit for approval")
        report.status = ReportStatusEnum.ON_APPROVAL
        if approver_id is not None:
            report.approver_id = approver_id
        if comment:
            report.last_comment = comment
        self.db.flush()
        return report

    def approve(self, report: Report, *, comment: str | None = None) -> Report:
        self._ensure_status(report, {ReportStatusEnum.ON_APPROVAL}, "approve")
        report.status = ReportStatusEnum.APPROVED
        report.approved_at = datetime.now(timezone.utc)
        report.rejected_at = None
        if comment:
            report.last_comment = comment
        self.db.flush()
        return report

    def reject(self, report: Report, *, comment: str | None = None) -> Report:
        self._ensure_status(report, {ReportStatusEnum.ON_REVIEW, ReportStatusEnum.ON_APPROVAL}, "reject")
        report.status = ReportStatusEnum.REJECTED
        report.rejected_at = datetime.now(timezone.utc)
        if comment:
            report.last_comment = comment
        self.db.flush()
        return report

    def send_to_rework(self, report: Report, *, comment: str | None = None) -> Report:
        self._ensure_status(report, {ReportStatusEnum.REJECTED, ReportStatusEnum.FAILED}, "send to rework")
        report.status = ReportStatusEnum.REWORK
        if comment:
            report.last_comment = comment
        self.db.flush()
        return report

    def archive(self, report: Report, *, comment: str | None = None) -> Report:
        self._ensure_status(
            report,
            {ReportStatusEnum.APPROVED, ReportStatusEnum.REJECTED, ReportStatusEnum.FAILED},
            "archive",
        )
        report.status = ReportStatusEnum.ARCHIVED
        report.is_archived = True
        if comment:
            report.last_comment = comment
        self.db.flush()
        return report

    def transition_report_status(
        self,
        report: Report,
        *,
        target_status: ReportStatusEnum,
        comment: str | None = None,
        current_assignee_id: int | None = None,
        approver_id: int | None = None,
    ) -> Report:
        target_status = ReportStatusEnum(target_status)
        if target_status == ReportStatusEnum.ON_REVIEW:
            return self.submit_for_review(report, comment=comment, current_assignee_id=current_assignee_id)
        if target_status == ReportStatusEnum.ON_APPROVAL:
            return self.submit_for_approval(report, comment=comment, approver_id=approver_id)
        if target_status == ReportStatusEnum.APPROVED:
            return self.approve(report, comment=comment)
        if target_status == ReportStatusEnum.REJECTED:
            return self.reject(report, comment=comment)
        if target_status == ReportStatusEnum.REWORK:
            return self.send_to_rework(report, comment=comment)
        if target_status == ReportStatusEnum.ARCHIVED:
            return self.archive(report, comment=comment)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Manual transition to status '{self._value(target_status)}' is not allowed.",
        )

    @staticmethod
    def _value(status_value: ReportStatusEnum | str) -> str:
        return status_value.value if hasattr(status_value, "value") else str(status_value)

    def _ensure_status(self, report: Report, allowed: set[ReportStatusEnum], action: str) -> None:
        current = ReportStatusEnum(report.status)
        if current not in allowed:
            allowed_text = ", ".join(sorted(item.value for item in allowed))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Cannot {action} report from status '{current.value}'. "
                    f"Allowed statuses: {allowed_text}."
                ),
            )