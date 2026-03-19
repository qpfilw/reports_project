from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin_user
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.processing_task import ProcessingTask
from app.models.project import Project
from app.models.report import Report
from app.models.user import User
from app.schemas.admin import AdminOverview

router = APIRouter(dependencies=[Depends(require_admin_user)])

@router.get("/overview", response_model=AdminOverview)
def admin_overview(db: Session = Depends(get_db)) -> AdminOverview:
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    active_users = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
    blocked_users = db.scalar(select(func.count()).select_from(User).where(User.is_blocked.is_(True))) or 0

    total_projects = db.scalar(select(func.count()).select_from(Project)) or 0
    archived_projects = db.scalar(select(func.count()).select_from(Project).where(Project.is_archived.is_(True))) or 0

    total_reports = db.scalar(select(func.count()).select_from(Report)) or 0
    total_tasks = db.scalar(select(func.count()).select_from(ProcessingTask)) or 0
    total_failed_tasks = db.scalar(
        select(func.count()).select_from(ProcessingTask).where(ProcessingTask.status == "failed")
    ) or 0

    total_notifications = db.scalar(select(func.count()).select_from(Notification)) or 0
    unread_notifications = db.scalar(
        select(func.count()).select_from(Notification).where(Notification.is_read.is_(False))
    ) or 0

    total_audit_logs = db.scalar(select(func.count()).select_from(AuditLog)) or 0

    return AdminOverview(
        total_users=total_users,
        active_users=active_users,
        blocked_users=blocked_users,
        total_projects=total_projects,
        archived_projects=archived_projects,
        total_reports=total_reports,
        total_tasks=total_tasks,
        total_failed_tasks=total_failed_tasks,
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
        total_audit_logs=total_audit_logs,
    )