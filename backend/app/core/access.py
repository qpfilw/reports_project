from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import AccessDeniedError, ObjectNotFoundError, ProjectScopeMismatchError, TemplateMismatchError, raise_http
from app.core.permissions import (
    can_manage_project,
    can_read_project,
    can_write_project,
    is_admin,
    is_pending,
)
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
        raise_http(
            ObjectNotFoundError(
                detail="Project not found.",
                code="PROJECT_NOT_FOUND",
            )
        )
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

    membership = None
    if not is_admin(current_user) and project.owner_id != current_user.id:
        membership = get_project_membership(
            db,
            project_id=project_id,
            user_id=current_user.id,
            access_statuses=[ProjectAccessStatusEnum.APPROVED],
        )

    if not can_read_project(user=current_user, project=project, membership=membership):
        raise_http(
            AccessDeniedError(
                detail="You do not have approved access to this project.",
                code="PROJECT_READ_ACCESS_DENIED",
                extra={"project_id": project_id},
            )
        )

    return project


def ensure_project_write_access(db: Session, *, project_id: int, current_user: User) -> Project:
    project = get_project_or_404(db, project_id)

    membership = None
    if not is_admin(current_user) and project.owner_id != current_user.id:
        membership = get_project_membership(
            db,
            project_id=project_id,
            user_id=current_user.id,
            access_statuses=[ProjectAccessStatusEnum.APPROVED],
        )

    if not can_write_project(user=current_user, project=project, membership=membership):
        raise_http(
            AccessDeniedError(
                detail="You do not have write access to this project.",
                code="PROJECT_WRITE_ACCESS_DENIED",
                extra={"project_id": project_id},
            )
        )

    return project


def ensure_project_owner_or_admin(db: Session, *, project_id: int, current_user: User) -> Project:
    project = get_project_or_404(db, project_id)

    membership = None
    if not is_admin(current_user) and project.owner_id != current_user.id:
        membership = get_project_membership(
            db,
            project_id=project_id,
            user_id=current_user.id,
            access_statuses=[ProjectAccessStatusEnum.APPROVED],
        )

    if not can_manage_project(user=current_user, project=project, membership=membership):
        raise_http(
            AccessDeniedError(
                detail="Only the project owner or administrator can perform this action.",
                code="PROJECT_MANAGE_ACCESS_DENIED",
                extra={"project_id": project_id},
            )
        )

    return project


def ensure_self_or_admin(*, current_user: User, target_user_id: int) -> None:
    if is_admin(current_user) or current_user.id == target_user_id:
        return

    raise_http(
        AccessDeniedError(
            detail="You can only access your own resources.",
            code="SELF_ACCESS_REQUIRED",
            extra={"target_user_id": target_user_id},
        )
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
        raise_http(
            AccessDeniedError(
                detail="The selected user does not have approved access to this project.",
                code="PROJECT_MEMBERSHIP_REQUIRED",
                extra={"project_id": project_id, "user_id": user_id},
            )
        )


def ensure_template_matches_report_type(*, template, report_type_id: int) -> None:
    if template is None:
        return

    target_report_type_id = getattr(template, "target_report_type_id", None)
    if target_report_type_id is not None and target_report_type_id != report_type_id:
        raise_http(
            TemplateMismatchError(
                detail="ML template does not match the report type.",
                extra={
                    "template_target_report_type_id": target_report_type_id,
                    "report_type_id": report_type_id,
                },
            )
        )


def ensure_same_project_scope(*, left_project_id: int | None, right_project_id: int | None, object_name: str = "Objects") -> None:
    if left_project_id is None or right_project_id is None:
        return
    if left_project_id != right_project_id:
        raise_http(
            ProjectScopeMismatchError(
                detail=f"{object_name} belong to different projects.",
                extra={
                    "left_project_id": left_project_id,
                    "right_project_id": right_project_id,
                },
            )
        )