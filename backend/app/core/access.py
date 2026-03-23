from __future__ import annotations
from collections.abc import Iterable
from fastapi import HTTPException, status
from sqlalchemy import Select, exists, literal, or_, select
from sqlalchemy.orm import Session
from app.models.enums import ProjectAccessStatusEnum, ProjectMemberRoleEnum, RoleCodeEnum
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User

PROJECT_WRITE_ROLES: set[ProjectMemberRoleEnum] = {
    ProjectMemberRoleEnum.OWNER,
    ProjectMemberRoleEnum.MANAGER,
    ProjectMemberRoleEnum.EDITOR,
}

def get_role_code(user: User) -> RoleCodeEnum | str:
    return user.role.code.value if hasattr(user.role.code, "value") else str(user.role.code)

def is_admin(user: User) -> bool:
    return get_role_code(user) == RoleCodeEnum.ADMIN.value

def is_pending(user: User) -> bool:
    return get_role_code(user) == RoleCodeEnum.PENDING.value

def approved_project_ids_subquery(user: User):
    membership_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == user.id,
        ProjectMember.access_status == ProjectAccessStatusEnum.APPROVED,
    )

    return select(Project.id).where(
        or_(
            Project.owner_id == user.id,
            Project.id.in_(membership_projects),
        )
    )

def apply_project_scope(stmt: Select, *, project_column, current_user: User) -> Select:
    if is_admin(current_user):
        return stmt
    return stmt.where(project_column.in_(approved_project_ids_subquery(current_user)))

def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project

def get_project_membership(
    db: Session,
    *,
    project_id: int,
    user_id: int,
    access_statuses: Iterable[ProjectAccessStatusEnum] | None = None,
) -> ProjectMember | None:
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    )
    if access_statuses is not None:
        stmt = stmt.where(ProjectMember.access_status.in_(tuple(access_statuses)))
    return db.scalar(stmt)

def ensure_project_read_access(db: Session, *, project_id: int, current_user: User) -> Project:
    project = get_project_or_404(db, project_id)
    if is_admin(current_user) or project.owner_id == current_user.id:
        return project

    membership = get_project_membership(
        db,
        project_id=project_id,
        user_id=current_user.id,
        access_statuses=[ProjectAccessStatusEnum.APPROVED],
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have approved access to this project.",
        )
    return project

def ensure_project_write_access(db: Session, *, project_id: int, current_user: User) -> Project:
    project = ensure_project_read_access(db, project_id=project_id, current_user=current_user)
    if is_admin(current_user) or project.owner_id == current_user.id:
        return project

    membership = get_project_membership(
        db,
        project_id=project_id,
        user_id=current_user.id,
        access_statuses=[ProjectAccessStatusEnum.APPROVED],
    )
    if membership is None or membership.member_role not in PROJECT_WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have write access to this project.",
        )
    return project

def ensure_project_owner_or_admin(db: Session, *, project_id: int, current_user: User) -> Project:
    project = get_project_or_404(db, project_id)
    if is_admin(current_user) or project.owner_id == current_user.id:
        return project
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only the project owner or administrator can perform this action.",
    )

def ensure_self_or_admin(*, current_user: User, target_user_id: int) -> None:
    if is_admin(current_user) or current_user.id == target_user_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only access your own resources.",
    )


def ensure_user_has_project_membership(
    db: Session,
    *,
    project_id: int,
    user_id: int,
    allow_owner: bool = True,
) -> None:
    project = get_project_or_404(db, project_id)
    if allow_owner and project.owner_id == user_id:
        return

    membership = get_project_membership(
        db,
        project_id=project_id,
        user_id=user_id,
        access_statuses=[ProjectAccessStatusEnum.APPROVED],
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The selected user does not have approved access to this project.",
        )


def ensure_template_matches_report_type(*, template, report_type_id: int) -> None:
    if template is None:
        return
    target_report_type_id = getattr(template, "target_report_type_id", None)
    if target_report_type_id is not None and target_report_type_id != report_type_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ML template does not match the report type.",
        )