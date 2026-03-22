from __future__ import annotations
from datetime import date, datetime
from pydantic import Field, field_validator
from app.models.enums import ReportStatusEnum
from .common import BaseSchema, IdSchema, TimestampSchema
from .template import MlTemplateShortRead
from .user import UserShortRead

def _parse_flexible_date(value: object) -> object:
    if value is None or isinstance(value, date):
        return value

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return value

        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass

    return value

class ReportTypeCreate(BaseSchema):
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    schema_version: str = Field(default="1.0", max_length=50)
    is_active: bool = True

class ReportTypeUpdate(BaseSchema):
    code: str | None = Field(None, min_length=2, max_length=100)
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    schema_version: str | None = Field(None, max_length=50)
    is_active: bool | None = None

class ReportTypeShortRead(IdSchema):
    code: str
    name: str
    schema_version: str
    is_active: bool

class ReportTypeRead(TimestampSchema, IdSchema):
    code: str
    name: str
    description: str | None = None
    schema_version: str
    is_active: bool

class ReportCreate(BaseSchema):
    project_id: int
    report_type_id: int
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    report_period_start: date
    report_period_end: date
    creator_id: int
    current_assignee_id: int | None = None
    approver_id: int | None = None
    ml_template_id: int | None = None

    @field_validator("report_period_start", "report_period_end", mode="before")
    @classmethod
    def parse_report_dates(cls, value: object) -> object:
        return _parse_flexible_date(value)

class ReportUpdate(BaseSchema):
    report_type_id: int | None = None
    title: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    report_period_start: date | None = None
    report_period_end: date | None = None
    current_assignee_id: int | None = None
    approver_id: int | None = None
    ml_template_id: int | None = None
    version: int | None = Field(None, ge=1)
    last_comment: str | None = None
    is_archived: bool | None = None

    @field_validator("report_period_start", "report_period_end", mode="before")
    @classmethod
    def parse_report_dates(cls, value: object) -> object:
        return _parse_flexible_date(value)

class ReportStatusUpdate(BaseSchema):
    status: ReportStatusEnum
    last_comment: str | None = None
    current_assignee_id: int | None = None
    approver_id: int | None = None
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None

class ReportShortRead(IdSchema):
    project_id: int
    report_type_id: int
    title: str
    status: ReportStatusEnum
    report_period_start: date
    report_period_end: date
    version: int
    is_archived: bool

class ReportRead(TimestampSchema, IdSchema):
    project_id: int
    report_type_id: int
    title: str
    description: str | None = None
    report_period_start: date
    report_period_end: date
    status: ReportStatusEnum
    creator_id: int
    current_assignee_id: int | None = None
    approver_id: int | None = None
    ml_template_id: int | None = None
    version: int
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    last_comment: str | None = None
    is_archived: bool

class ReportDetailRead(ReportRead):
    report_type: ReportTypeShortRead
    creator: UserShortRead
    current_assignee: UserShortRead | None = None
    approver: UserShortRead | None = None
    ml_template: MlTemplateShortRead | None = None