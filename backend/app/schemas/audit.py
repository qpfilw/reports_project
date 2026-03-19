from __future__ import annotations
from datetime import datetime
from typing import Any
from app.models.enums import AuditActionEnum, AuditEntityTypeEnum
from .common import BaseSchema, IdSchema
from .project import ProjectRead
from .user import UserShortRead

class AuditLogCreate(BaseSchema):
    user_id: int | None = None
    project_id: int | None = None
    action: AuditActionEnum
    entity_type: AuditEntityTypeEnum
    entity_id: int | None = None
    before_json: dict[str, Any] | None = None
    after_json: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None

class AuditLogRead(IdSchema):
    user_id: int | None = None
    project_id: int | None = None
    action: AuditActionEnum
    entity_type: AuditEntityTypeEnum
    entity_id: int | None = None
    before_json: dict[str, Any] | None = None
    after_json: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

class AuditLogDetailRead(AuditLogRead):
    user: UserShortRead | None = None
    project: ProjectRead | None = None