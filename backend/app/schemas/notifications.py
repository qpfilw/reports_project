from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import Field
from app.models.enums import NotificationTypeEnum
from .common import BaseSchema, IdSchema
from .processing import ProcessingTaskShortRead
from .project import ProjectRead
from .report import ReportShortRead
from .user import UserShortRead

class NotificationCreate(BaseSchema):
    user_id: int
    project_id: int | None = None
    report_id: int | None = None
    processing_task_id: int | None = None
    type: NotificationTypeEnum
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    payload_json: dict[str, Any] = Field(default_factory=dict)
    is_read: bool = False

class NotificationUpdate(BaseSchema):
    title: str | None = Field(None, min_length=1, max_length=255)
    message: str | None = Field(None, min_length=1)
    payload_json: dict[str, Any] | None = None
    is_read: bool | None = None
    read_at: datetime | None = None

class NotificationRead(IdSchema):
    user_id: int
    project_id: int | None = None
    report_id: int | None = None
    processing_task_id: int | None = None
    type: NotificationTypeEnum
    title: str
    message: str
    payload_json: dict[str, Any]
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

class NotificationDetailRead(NotificationRead):
    user: UserShortRead
    project: ProjectRead | None = None
    report: ReportShortRead | None = None
    processing_task: ProcessingTaskShortRead | None = None