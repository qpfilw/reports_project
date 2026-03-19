from __future__ import annotations
from datetime import datetime
from pydantic import Field
from .common import BaseSchema, IdSchema
from .report import ReportShortRead, ReportTypeShortRead
from .user import UserShortRead

class ReportUploadCreate(BaseSchema):
    report_id: int
    project_id: int
    report_type_id: int
    uploaded_by: int
    original_filename: str = Field(..., min_length=1, max_length=255)
    storage_path: str = Field(..., min_length=1, max_length=512)
    content_type: str | None = Field(None, max_length=255)
    file_size: int = Field(..., ge=0)
    checksum_sha256: str | None = Field(None, min_length=64, max_length=64)
    is_latest: bool = True
    upload_version: int = Field(default=1, ge=1)
    comment: str | None = None

class ReportUploadUpdate(BaseSchema):
    is_latest: bool | None = None
    comment: str | None = None

class ReportUploadShortRead(IdSchema):
    report_id: int
    project_id: int
    report_type_id: int
    uploaded_by: int
    original_filename: str
    upload_version: int
    is_latest: bool
    uploaded_at: datetime

class ReportUploadRead(IdSchema):
    report_id: int
    project_id: int
    report_type_id: int
    uploaded_by: int
    original_filename: str
    storage_path: str
    content_type: str | None = None
    file_size: int
    checksum_sha256: str | None = None
    is_latest: bool
    upload_version: int
    uploaded_at: datetime
    comment: str | None = None

class ReportUploadDetailRead(ReportUploadRead):
    report: ReportShortRead
    report_type: ReportTypeShortRead
    uploader: UserShortRead