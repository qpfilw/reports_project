from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import Field
from app.models.enums import ProcessingLogLevelEnum, ProcessingStatusEnum
from .common import BaseSchema, IdSchema, CreatedAtSchema
from .report import ReportShortRead
from .template import MlTemplateShortRead
from .upload import ReportUploadShortRead
from .user import UserShortRead

class ProcessingTaskLaunchRequest(BaseSchema):
    report_id: int
    report_upload_id: int
    ml_template_id: int | None = None
    created_by: int | None = None
    priority: int = Field(default=5, ge=1, le=10)
    params_json: dict[str, Any] = Field(default_factory=dict)

class ProcessingTaskUpdate(BaseSchema):
    ml_template_id: int | None = None
    status: ProcessingStatusEnum | None = None
    priority: int | None = Field(None, ge=1, le=10)
    progress: int | None = Field(None, ge=0, le=100)
    params_json: dict[str, Any] | None = None
    quality_score: float | None = Field(None, ge=0, le=1)
    warning_count: int | None = Field(None, ge=0)
    error_count: int | None = Field(None, ge=0)
    retry_count: int | None = Field(None, ge=0)
    error_summary: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

class ProcessingTaskShortRead(IdSchema):
    report_id: int
    report_upload_id: int
    ml_template_id: int | None = None
    status: ProcessingStatusEnum
    progress: int
    priority: int
    created_at: datetime

class ProcessingTaskRead(CreatedAtSchema, IdSchema):
    report_id: int
    report_upload_id: int
    ml_template_id: int | None = None
    created_by: int | None = None
    celery_task_id: str | None = None
    status: ProcessingStatusEnum
    priority: int
    progress: int
    params_json: dict[str, Any]
    quality_score: float | None = None
    warning_count: int
    error_count: int
    retry_count: int
    error_summary: str | None = None
    queued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

class ProcessingLogCreate(BaseSchema):
    processing_task_id: int
    level: ProcessingLogLevelEnum
    stage: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1)
    context_json: dict[str, Any] = Field(default_factory=dict)

class ProcessingLogRead(IdSchema):
    processing_task_id: int
    level: ProcessingLogLevelEnum
    stage: str
    message: str
    context_json: dict[str, Any]
    created_at: datetime

class TaskErrorCreate(BaseSchema):
    processing_task_id: int
    error_code: str = Field(..., min_length=1, max_length=100)
    error_type: str = Field(..., min_length=1, max_length=100)
    field_path: str | None = Field(None, max_length=255)
    row_number: int | None = Field(None, ge=1)
    source_value: str | None = None
    details: str | None = None
    is_critical: bool = False

class TaskErrorRead(IdSchema):
    processing_task_id: int
    error_code: str
    error_type: str
    field_path: str | None = None
    row_number: int | None = None
    source_value: str | None = None
    details: str | None = None
    is_critical: bool
    created_at: datetime

class ProcessingTaskDetailRead(ProcessingTaskRead):
    report: ReportShortRead
    report_upload: ReportUploadShortRead
    ml_template: MlTemplateShortRead | None = None
    creator: UserShortRead | None = None
    logs: list[ProcessingLogRead] = Field(default_factory=list)
    errors: list[TaskErrorRead] = Field(default_factory=list)