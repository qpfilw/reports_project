from __future__ import annotations
from typing import Any
from app.models.enums import (
    ProjectAccessStatusEnum,
    ProjectMemberRoleEnum,
    ReportStatusEnum,
    RoleCodeEnum,
)

def _role_code_value(user: Any) -> str | None:
    if user is None:
        return None

    role = getattr(user, "role", None)
    if role is not None:
        code = getattr(role, "code", None)
        if code is not None:
            return code.value if hasattr(code, "value") else str(code)

    code = getattr(user, "role_code", None)
    if code is not None:
        return code.value if hasattr(code, "value") else str(code)

    return None

def _access_status_value(membership: Any) -> str | None:
    if membership is None:
        return None
    access_status = getattr(membership, "access_status", None)
    if access_status is None:
        return None
    return access_status.value if hasattr(access_status, "value") else str(access_status)

def _member_role_value(membership: Any) -> str | None:
    if membership is None:
        return None
    member_role = getattr(membership, "member_role", None)
    if member_role is None:
        return None
    return member_role.value if hasattr(member_role, "value") else str(member_role)

def _report_status_value(report: Any) -> str | None:
    if report is None:
        return None
    report_status = getattr(report, "status", None)
    if report_status is None:
        return None
    return report_status.value if hasattr(report_status, "value") else str(report_status)

def is_admin(user: Any) -> bool:
    return _role_code_value(user) == RoleCodeEnum.ADMIN.value

def is_manager(user: Any) -> bool:
    return _role_code_value(user) == RoleCodeEnum.MANAGER.value

def is_operator(user: Any) -> bool:
    return _role_code_value(user) == RoleCodeEnum.OPERATOR.value

def is_viewer(user: Any) -> bool:
    return _role_code_value(user) == RoleCodeEnum.VIEWER.value

def is_pending(user: Any) -> bool:
    return _role_code_value(user) == RoleCodeEnum.PENDING.value

def is_active_user(user: Any) -> bool:
    if user is None:
        return False
    return bool(getattr(user, "is_active", False)) and not bool(getattr(user, "is_blocked", False))

def can_use_platform(user: Any) -> bool:
    if not is_active_user(user):
        return False
    return _role_code_value(user) in {
        RoleCodeEnum.ADMIN.value,
        RoleCodeEnum.MANAGER.value,
        RoleCodeEnum.OPERATOR.value,
        RoleCodeEnum.VIEWER.value,
    }

def membership_is_approved(membership: Any) -> bool:
    return _access_status_value(membership) == ProjectAccessStatusEnum.APPROVED.value

def can_read_project(*, user: Any, project: Any, membership: Any = None) -> bool:
    if not can_use_platform(user):
        return False

    if is_admin(user):
        return True

    if project is not None and getattr(project, "owner_id", None) == getattr(user, "id", None):
        return True

    return membership_is_approved(membership)

def can_write_project(*, user: Any, project: Any, membership: Any = None) -> bool:
    if not can_use_platform(user):
        return False

    if is_admin(user):
        return True

    if project is not None and getattr(project, "owner_id", None) == getattr(user, "id", None):
        return True

    if not membership_is_approved(membership):
        return False

    member_role = _member_role_value(membership)
    return member_role in {
        ProjectMemberRoleEnum.EDITOR.value,
        ProjectMemberRoleEnum.MANAGER.value,
    } or is_manager(user) or is_operator(user)

def can_manage_project(*, user: Any, project: Any, membership: Any = None) -> bool:
    if not can_use_platform(user):
        return False

    if is_admin(user):
        return True

    if project is not None and getattr(project, "owner_id", None) == getattr(user, "id", None):
        return True

    if not membership_is_approved(membership):
        return False

    return _member_role_value(membership) == ProjectMemberRoleEnum.MANAGER.value or is_manager(user)

def can_review_project_access(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_manage_project(user=user, project=project, membership=membership)

def can_assign_project_users(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_manage_project(user=user, project=project, membership=membership)

def can_create_report(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_write_project(user=user, project=project, membership=membership)

def can_update_report(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_write_project(user=user, project=project, membership=membership)

def can_submit_report_for_review(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_write_project(user=user, project=project, membership=membership)

def can_submit_report_for_approval(*, user: Any, project: Any, membership: Any = None) -> bool:
    if is_admin(user):
        return True
    if not can_use_platform(user):
        return False
    if project is not None and getattr(project, "owner_id", None) == getattr(user, "id", None):
        return True
    if not membership_is_approved(membership):
        return False
    return is_manager(user) or _member_role_value(membership) == ProjectMemberRoleEnum.MANAGER.value

def can_approve_report(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_submit_report_for_approval(user=user, project=project, membership=membership)

def can_reject_report(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_submit_report_for_approval(user=user, project=project, membership=membership)

def can_send_report_to_rework(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_write_project(user=user, project=project, membership=membership)

def can_launch_processing(*, user: Any, project: Any, membership: Any = None, report: Any = None) -> bool:
    if not can_write_project(user=user, project=project, membership=membership):
        return False

    report_status = _report_status_value(report)
    return report_status in {
        ReportStatusEnum.DRAFT.value,
        ReportStatusEnum.UPLOADED.value,
        ReportStatusEnum.FAILED.value,
        ReportStatusEnum.REWORK.value,
    }

def can_download_artifact(*, user: Any, project: Any, membership: Any = None) -> bool:
    return can_read_project(user=user, project=project, membership=membership)

def can_manage_users(*, user: Any) -> bool:
    return is_admin(user)

def can_manage_roles(*, user: Any) -> bool:
    return is_admin(user)

def can_manage_admin_panel(*, user: Any) -> bool:
    return is_admin(user)

def can_view_notifications(*, user: Any, target_user_id: int | None = None) -> bool:
    if not can_use_platform(user):
        return False
    if is_admin(user):
        return True
    if target_user_id is None:
        return True
    return getattr(user, "id", None) == target_user_id

def can_manage_notification_state(*, user: Any, target_user_id: int | None = None) -> bool:
    return can_view_notifications(user=user, target_user_id=target_user_id)