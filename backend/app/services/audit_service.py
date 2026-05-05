from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.dashboard import Dashboard
from app.models.enums import AuditActionEnum, AuditEntityTypeEnum
from app.models.export_artifact import ExportArtifact
from app.models.ml_template import MlTemplate
from app.models.processing_task import ProcessingTask
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.report import Report
from app.models.report_type import ReportType
from app.models.report_upload import ReportUpload
from app.models.user import User


def _serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]
    return value


def _with_changed_fields(before: dict[str, Any] | None, after: dict[str, Any] | None) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if before is None and after is None:
        return None, None

    before_data = dict(before or {})
    after_data = dict(after or {})
    changed_fields = sorted(
        field
        for field in set(before_data) | set(after_data)
        if before_data.get(field) != after_data.get(field)
    )
    if changed_fields:
        after_data["_changed_fields"] = changed_fields
    return before_data or None, after_data or None


def get_request_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    return request.client.host


def get_request_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.headers.get("user-agent")


def log_audit(
    db: Session,
    *,
    action: AuditActionEnum,
    entity_type: AuditEntityTypeEnum,
    entity_id: int | None = None,
    actor: User | None = None,
    project_id: int | None = None,
    before_json: dict[str, Any] | None = None,
    after_json: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    before_json, after_json = _with_changed_fields(before_json, after_json)
    audit_log = AuditLog(
        user_id=actor.id if actor is not None else None,
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=_serialize(before_json),
        after_json=_serialize(after_json),
        ip_address=get_request_ip(request),
        user_agent=get_request_user_agent(request),
    )
    db.add(audit_log)
    return audit_log


def snapshot_user(user: User | None) -> dict[str, Any] | None:
    if user is None:
        return None
    role_code = None
    if getattr(user, "role", None) is not None:
        role_code = getattr(user.role.code, "value", user.role.code)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "position": user.position,
        "department": user.department,
        "is_active": user.is_active,
        "is_blocked": user.is_blocked,
        "role_id": user.role_id,
        "role_code": role_code,
        "last_login_at": user.last_login_at,
    }


def snapshot_project(project: Project | None) -> dict[str, Any] | None:
    if project is None:
        return None
    return {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "description": project.description,
        "owner_id": project.owner_id,
        "is_archived": project.is_archived,
        "created_at": getattr(project, "created_at", None),
        "updated_at": getattr(project, "updated_at", None),
    }


def snapshot_project_member(member: ProjectMember | None) -> dict[str, Any] | None:
    if member is None:
        return None
    return {
        "id": member.id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "member_role": member.member_role,
        "access_status": member.access_status,
        "added_by": member.added_by,
        "requested_at": member.requested_at,
        "request_note": member.request_note,
        "reviewed_by": member.reviewed_by,
        "reviewed_at": member.reviewed_at,
        "review_note": member.review_note,
    }


def snapshot_report(report: Report | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "id": report.id,
        "project_id": report.project_id,
        "report_type_id": report.report_type_id,
        "creator_id": report.creator_id,
        "title": report.title,
        "description": report.description,
        "status": report.status,
        "report_period_start": report.report_period_start,
        "report_period_end": report.report_period_end,
        "current_assignee_id": report.current_assignee_id,
        "approver_id": report.approver_id,
        "ml_template_id": report.ml_template_id,
        "last_comment": report.last_comment,
        "is_archived": report.is_archived,
        "submitted_at": report.submitted_at,
        "approved_at": report.approved_at,
        "rejected_at": report.rejected_at,
    }


def snapshot_report_upload(upload: ReportUpload | None) -> dict[str, Any] | None:
    if upload is None:
        return None
    return {
        "id": upload.id,
        "project_id": upload.project_id,
        "report_id": upload.report_id,
        "report_type_id": upload.report_type_id,
        "storage_path": upload.storage_path,
        "original_filename": getattr(upload, "original_filename", None),
        "content_type": getattr(upload, "content_type", None),
        "file_size": upload.file_size,
        "checksum_sha256": upload.checksum_sha256,
        "is_latest": upload.is_latest,
        "upload_version": upload.upload_version,
        "comment": upload.comment,
        "uploaded_by": upload.uploaded_by,
        "uploaded_at": getattr(upload, "uploaded_at", None),
    }


def snapshot_processing_task(task: ProcessingTask | None) -> dict[str, Any] | None:
    if task is None:
        return None
    return {
        "id": task.id,
        "report_id": task.report_id,
        "report_upload_id": task.report_upload_id,
        "ml_template_id": task.ml_template_id,
        "created_by": task.created_by,
        "status": task.status,
        "priority": task.priority,
        "progress": task.progress,
        "quality_score": task.quality_score,
        "warning_count": task.warning_count,
        "error_count": task.error_count,
        "retry_count": task.retry_count,
        "error_summary": task.error_summary,
        "queued_at": task.queued_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "params_json": task.params_json,
    }


def snapshot_export(export: ExportArtifact | None) -> dict[str, Any] | None:
    if export is None:
        return None
    return {
        "id": export.id,
        "processing_task_id": export.processing_task_id,
        "report_id": export.report_id,
        "dashboard_id": export.dashboard_id,
        "created_by": export.created_by,
        "format": export.format,
        "storage_path": export.storage_path,
        "file_size": export.file_size,
        "created_at": getattr(export, "created_at", None),
    }


def snapshot_template(template: MlTemplate | None) -> dict[str, Any] | None:
    if template is None:
        return None
    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "description": template.description,
        "template_type": template.template_type,
        "target_report_type_id": template.target_report_type_id,
        "department": template.department,
        "version": template.version,
        "is_default": template.is_default,
        "is_active": template.is_active,
        "model_path": template.model_path,
        "created_by": template.created_by,
    }


def snapshot_report_type(report_type: ReportType | None) -> dict[str, Any] | None:
    if report_type is None:
        return None
    return {
        "id": report_type.id,
        "code": report_type.code,
        "name": report_type.name,
        "description": report_type.description,
        "schema_version": report_type.schema_version,
        "is_active": report_type.is_active,
    }


def snapshot_dashboard(dashboard: Dashboard | None) -> dict[str, Any] | None:
    if dashboard is None:
        return None
    return {
        "id": dashboard.id,
        "project_id": dashboard.project_id,
        "report_id": dashboard.report_id,
        "normalized_dataset_id": dashboard.normalized_dataset_id,
        "owner_id": dashboard.owner_id,
        "name": dashboard.name,
        "description": dashboard.description,
        "dashboard_type": dashboard.dashboard_type,
        "source_type": dashboard.source_type,
        "is_shared": dashboard.is_shared,
        "is_default": dashboard.is_default,
        "last_generated_at": dashboard.last_generated_at,
    }
