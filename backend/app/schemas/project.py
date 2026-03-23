from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.models.enums import ProjectAccessStatusEnum, ProjectMemberRoleEnum
from .common import BaseSchema, IdSchema, TimestampSchema
from .user import UserShortRead


class ProjectAccessRequestCreate(BaseSchema):
    member_role: ProjectMemberRoleEnum = ProjectMemberRoleEnum.VIEWER
    request_note: str | None = Field(None, max_length=1000)


class ProjectAccessReviewRequest(BaseSchema):
    member_role: ProjectMemberRoleEnum | None = None
    review_note: str | None = Field(None, max_length=1000)


class ProjectMemberCreate(BaseSchema):
    user_id: int
    member_role: ProjectMemberRoleEnum
    request_note: str | None = Field(None, max_length=1000)


class ProjectMemberUpdate(BaseSchema):
    member_role: ProjectMemberRoleEnum | None = None
    review_note: str | None = Field(None, max_length=1000)


class ProjectMemberRead(IdSchema):
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


class ProjectMemberDetailRead(ProjectMemberRead):
    user: UserShortRead
    creator: UserShortRead | None = None
    reviewer: UserShortRead | None = None


class ProjectCreate(BaseSchema):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    owner_id: int


class ProjectUpdate(BaseSchema):
    name: str | None = Field(None, min_length=2, max_length=255)
    code: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None
    is_archived: bool | None = None


class ProjectRead(TimestampSchema, IdSchema):
    name: str
    code: str
    description: str | None = None
    owner_id: int
    is_archived: bool


class ProjectDetailRead(ProjectRead):
    owner: UserShortRead
    members: list[ProjectMemberDetailRead] = []
