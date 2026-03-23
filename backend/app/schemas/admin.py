from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.enums import ProjectAccessStatusEnum, ProjectMemberRoleEnum, RoleCodeEnum

from .common import BaseSchema, IdSchema
from .project import ProjectRead
from .user import UserDetailRead, UserShortRead


class AdminOverview(BaseSchema):
    total_users: int = 0
    active_users: int = 0
    blocked_users: int = 0
    pending_users: int = 0
    total_projects: int = 0
    archived_projects: int = 0
    total_reports: int = 0
    total_tasks: int = 0
    total_failed_tasks: int = 0
    total_notifications: int = 0
    unread_notifications: int = 0
    total_audit_logs: int = 0
    pending_project_access_requests: int = 0


class AdminUserApprovalRequest(BaseSchema):
    role_code: RoleCodeEnum = RoleCodeEnum.VIEWER


class AdminUserRoleUpdateRequest(BaseSchema):
    role_code: RoleCodeEnum


class AdminUserModerationRequest(BaseSchema):
    reason: str | None = Field(default=None, max_length=1000)


class AdminProjectAccessReviewRequest(BaseSchema):
    member_role: ProjectMemberRoleEnum | None = None
    review_note: str | None = Field(default=None, max_length=1000)


class AdminProjectAccessRequestRead(IdSchema):
    project_id: int
    user_id: int
    member_role: ProjectMemberRoleEnum
    access_status: ProjectAccessStatusEnum
    added_by: int | None = None
    added_at: datetime
    requested_at: datetime
    request_note: str | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    review_note: str | None = None
    project: ProjectRead
    user: UserShortRead
    creator: UserShortRead | None = None
    reviewer: UserShortRead | None = None


class AdminPendingUserRead(UserDetailRead):
    pass