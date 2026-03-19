from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.models.enums import ProcessingStatusEnum
from .common import BaseSchema

class TaskFilter(BaseSchema):
    report_id: int | None = None
    report_upload_id: int | None = None
    ml_template_id: int | None = None
    created_by: int | None = None
    status: ProcessingStatusEnum | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None

class TaskQueueInfo(BaseSchema):
    queued: int = 0
    running: int = 0
    failed: int = 0
    success: int = 0

class TaskProgressResponse(BaseSchema):
    task_id: int
    status: ProcessingStatusEnum
    progress: int = Field(..., ge=0, le=100)
    warning_count: int = 0
    error_count: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_summary: str | None = None