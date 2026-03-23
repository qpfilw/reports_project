from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_admin_user
from app.db.seed import get_role_by_code
from app.models.audit_log import AuditLog
from app.models.enums import ProjectAccessStatusEnum, RoleCodeEnum
from app.models.notification import Notification
from app.models.processing_task import ProcessingTask
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.report import Report
from app.models.role import Role
from app.models.user import User
from app.schemas.admin import (
    AdminOverview,
    AdminPendingUserRead,
    AdminProjectAccessRequestRead,
    AdminProjectAccessReviewRequest,
    AdminUserApprovalRequest,
    AdminUserModerationRequest,
    AdminUserRoleUpdateRequest,
)
from app.schemas.user import UserDetailRead

router = APIRouter(dependencies=[Depends(require_admin_user)])


def _get_user_detail_or_404(db: Session, user_id: int) -> User:
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def _get_project_access_request_or_404(db: Session, member_id: int) -> ProjectMember:
    stmt = (
        select(ProjectMember)
        .options(
            selectinload(ProjectMember.project).selectinload(Project.owner),
            selectinload(ProjectMember.user),
            selectinload(ProjectMember.creator),
            selectinload(ProjectMember.reviewer),
        )
        .where(ProjectMember.id == member_id)
    )
    member = db.scalar(stmt)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project access request not found.")
    return member


def _get_role_or_404(db: Session, role_code: RoleCodeEnum) -> Role:
    role = get_role_by_code(db, role_code)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return role


@router.get("/overview", response_model=AdminOverview)
def admin_overview(db: Session = Depends(get_db)) -> AdminOverview:
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    active_users = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
    blocked_users = db.scalar(select(func.count()).select_from(User).where(User.is_blocked.is_(True))) or 0
    pending_users = db.scalar(
        select(func.count())
        .select_from(User)
        .join(Role, Role.id == User.role_id)
        .where(Role.code == RoleCodeEnum.PENDING)
    ) or 0

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
    pending_project_access_requests = db.scalar(
        select(func.count())
        .select_from(ProjectMember)
        .where(ProjectMember.access_status == ProjectAccessStatusEnum.REQUESTED)
    ) or 0

    return AdminOverview(
        total_users=total_users,
        active_users=active_users,
        blocked_users=blocked_users,
        pending_users=pending_users,
        total_projects=total_projects,
        archived_projects=archived_projects,
        total_reports=total_reports,
        total_tasks=total_tasks,
        total_failed_tasks=total_failed_tasks,
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
        total_audit_logs=total_audit_logs,
        pending_project_access_requests=pending_project_access_requests,
    )


@router.get("/pending-users", response_model=list[AdminPendingUserRead])
def list_pending_users(db: Session = Depends(get_db)) -> list[User]:
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .join(Role, Role.id == User.role_id)
        .where(Role.code == RoleCodeEnum.PENDING)
        .order_by(User.created_at.desc(), User.id.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("/users/{user_id}/approve", response_model=UserDetailRead)
def approve_user(
    user_id: int,
    payload: AdminUserApprovalRequest,
    db: Session = Depends(get_db),
) -> User:
    user = _get_user_detail_or_404(db, user_id)
    if user.role.code != RoleCodeEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only users with pending role can be approved via this endpoint.",
        )

    if payload.role_code in {RoleCodeEnum.PENDING, RoleCodeEnum.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pending users can only be approved to viewer, operator or manager roles.",
        )

    role = _get_role_or_404(db, payload.role_code)
    user.role_id = role.id
    user.is_active = True
    user.is_blocked = False

    db.commit()
    db.refresh(user)
    return _get_user_detail_or_404(db, user.id)


@router.post("/users/{user_id}/reject", response_model=UserDetailRead)
def reject_user_registration(
    user_id: int,
    payload: AdminUserModerationRequest,
    db: Session = Depends(get_db),
) -> User:
    user = _get_user_detail_or_404(db, user_id)
    if user.role.code != RoleCodeEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only users with pending role can be rejected via this endpoint.",
        )

    user.is_active = False
    user.is_blocked = True
    db.commit()
    db.refresh(user)
    return _get_user_detail_or_404(db, user.id)


@router.post("/users/{user_id}/assign-role", response_model=UserDetailRead)
def assign_user_role(
    user_id: int,
    payload: AdminUserRoleUpdateRequest,
    db: Session = Depends(get_db),
) -> User:
    user = _get_user_detail_or_404(db, user_id)
    role = _get_role_or_404(db, payload.role_code)
    user.role_id = role.id
    db.commit()
    db.refresh(user)
    return _get_user_detail_or_404(db, user.id)


@router.post("/users/{user_id}/block", response_model=UserDetailRead)
def block_user(
    user_id: int,
    payload: AdminUserModerationRequest,
    db: Session = Depends(get_db),
) -> User:
    user = _get_user_detail_or_404(db, user_id)
    user.is_blocked = True
    db.commit()
    db.refresh(user)
    return _get_user_detail_or_404(db, user.id)


@router.post("/users/{user_id}/unblock", response_model=UserDetailRead)
def unblock_user(
    user_id: int,
    payload: AdminUserModerationRequest,
    db: Session = Depends(get_db),
) -> User:
    user = _get_user_detail_or_404(db, user_id)
    user.is_blocked = False
    user.is_active = True
    db.commit()
    db.refresh(user)
    return _get_user_detail_or_404(db, user.id)


@router.get("/project-access-requests", response_model=list[AdminProjectAccessRequestRead])
def list_project_access_requests(
    access_status: ProjectAccessStatusEnum = Query(default=ProjectAccessStatusEnum.REQUESTED),
    project_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ProjectMember]:
    stmt = (
        select(ProjectMember)
        .options(
            selectinload(ProjectMember.project).selectinload(Project.owner),
            selectinload(ProjectMember.user),
            selectinload(ProjectMember.creator),
            selectinload(ProjectMember.reviewer),
        )
        .where(ProjectMember.access_status == access_status)
        .order_by(ProjectMember.requested_at.desc(), ProjectMember.id.desc())
    )
    if project_id is not None:
        stmt = stmt.where(ProjectMember.project_id == project_id)
    return list(db.scalars(stmt).all())


@router.post("/project-access-requests/{member_id}/approve", response_model=AdminProjectAccessRequestRead)
def approve_project_access_request(
    member_id: int,
    payload: AdminProjectAccessReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user),
) -> ProjectMember:
    member = _get_project_access_request_or_404(db, member_id)
    member.access_status = ProjectAccessStatusEnum.APPROVED
    if payload.member_role is not None:
        member.member_role = payload.member_role
    member.reviewed_by = current_user.id
    member.reviewed_at = datetime.now(timezone.utc)
    member.review_note = payload.review_note
    if member.added_by is None:
        member.added_by = current_user.id

    db.commit()
    db.refresh(member)
    return _get_project_access_request_or_404(db, member.id)


@router.post("/project-access-requests/{member_id}/reject", response_model=AdminProjectAccessRequestRead)
def reject_project_access_request(
    member_id: int,
    payload: AdminProjectAccessReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user),
) -> ProjectMember:
    member = _get_project_access_request_or_404(db, member_id)
    member.access_status = ProjectAccessStatusEnum.REJECTED
    member.reviewed_by = current_user.id
    member.reviewed_at = datetime.now(timezone.utc)
    member.review_note = payload.review_note

    db.commit()
    db.refresh(member)
    return _get_project_access_request_or_404(db, member.id)