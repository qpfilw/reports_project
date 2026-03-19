from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import Field
from app.models.enums import DashboardSourceTypeEnum, DashboardTypeEnum
from .common import BaseSchema, IdSchema, TimestampSchema
from .report import ReportShortRead
from .result import NormalizedDatasetRead
from .user import UserShortRead

class DashboardCreate(BaseSchema):
    project_id: int
    report_id: int | None = None
    normalized_dataset_id: int | None = None
    owner_id: int
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    dashboard_type: DashboardTypeEnum
    source_type: DashboardSourceTypeEnum
    config_json: dict[str, Any] = Field(default_factory=dict)
    filters_json: dict[str, Any] = Field(default_factory=dict)
    layout_json: dict[str, Any] = Field(default_factory=dict)
    metrics_json: dict[str, Any] = Field(default_factory=dict)
    is_shared: bool = False
    is_default: bool = False

class DashboardUpdate(BaseSchema):
    report_id: int | None = None
    normalized_dataset_id: int | None = None
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    dashboard_type: DashboardTypeEnum | None = None
    source_type: DashboardSourceTypeEnum | None = None
    config_json: dict[str, Any] | None = None
    filters_json: dict[str, Any] | None = None
    layout_json: dict[str, Any] | None = None
    metrics_json: dict[str, Any] | None = None
    is_shared: bool | None = None
    is_default: bool | None = None
    last_generated_at: datetime | None = None

class DashboardShortRead(IdSchema):
    project_id: int
    report_id: int | None = None
    normalized_dataset_id: int | None = None
    owner_id: int
    name: str
    dashboard_type: DashboardTypeEnum
    source_type: DashboardSourceTypeEnum
    is_shared: bool
    is_default: bool

class DashboardRead(TimestampSchema, IdSchema):
    project_id: int
    report_id: int | None = None
    normalized_dataset_id: int | None = None
    owner_id: int
    name: str
    description: str | None = None
    dashboard_type: DashboardTypeEnum
    source_type: DashboardSourceTypeEnum
    config_json: dict[str, Any]
    filters_json: dict[str, Any]
    layout_json: dict[str, Any]
    metrics_json: dict[str, Any]
    is_shared: bool
    is_default: bool
    last_generated_at: datetime | None = None

class DashboardDetailRead(DashboardRead):
    owner: UserShortRead
    report: ReportShortRead | None = None
    normalized_dataset: NormalizedDatasetRead | None = None

class DashboardMetricItem(BaseSchema):
    key: str
    label: str
    value: int | float | str | None = None
    unit: str | None = None

class AnalyticsOverview(BaseSchema):
    total_reports: int = 0
    total_uploads: int = 0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_exports: int = 0
    average_quality_score: float | None = None
    metrics: list[DashboardMetricItem] = Field(default_factory=list)