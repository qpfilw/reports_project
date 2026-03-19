from __future__ import annotations
from datetime import datetime
from pydantic import Field
from app.models.enums import ExportFormatEnum
from .analytics import DashboardShortRead
from .common import BaseSchema, IdSchema
from .processing import ProcessingTaskShortRead
from .report import ReportShortRead
from .user import UserShortRead

class ExportArtifactCreate(BaseSchema):
    processing_task_id: int | None = None
    report_id: int | None = None
    dashboard_id: int | None = None
    format: ExportFormatEnum
    storage_path: str = Field(..., min_length=1, max_length=512)
    file_size: int = Field(..., ge=0)
    checksum_sha256: str | None = Field(None, min_length=64, max_length=64)
    created_by: int | None = None

class ExportArtifactRead(IdSchema):
    processing_task_id: int | None = None
    report_id: int | None = None
    dashboard_id: int | None = None
    format: ExportFormatEnum
    storage_path: str
    file_size: int
    checksum_sha256: str | None = None
    created_by: int | None = None
    created_at: datetime

class ExportArtifactDetailRead(ExportArtifactRead):
    processing_task: ProcessingTaskShortRead | None = None
    report: ReportShortRead | None = None
    dashboard: DashboardShortRead | None = None
    creator: UserShortRead | None = None

class ExportRequest(BaseSchema):
    processing_task_id: int | None = None
    report_id: int | None = None
    dashboard_id: int | None = None
    format: ExportFormatEnum