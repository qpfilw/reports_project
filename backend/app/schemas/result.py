from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import Field
from .common import BaseSchema, IdSchema
from .processing import ProcessingTaskShortRead
from .report import ReportShortRead

class NormalizedDatasetCreate(BaseSchema):
    processing_task_id: int
    report_id: int
    rows_count: int = Field(default=0, ge=0)
    schema_data: dict[str, Any] = Field(default_factory=dict, alias="schema_json")
    summary_json: dict[str, Any] = Field(default_factory=dict)
    preview_json: list[dict[str, Any]] = Field(default_factory=list)
    data_location: str = Field(..., min_length=1)

class NormalizedDatasetUpdate(BaseSchema):
    rows_count: int | None = Field(None, ge=0)
    schema_data: dict[str, Any] | None = Field(None, alias="schema_json")
    summary_json: dict[str, Any] | None = None
    preview_json: list[dict[str, Any]] | None = None
    data_location: str | None = None

class NormalizedDatasetRead(IdSchema):
    processing_task_id: int
    report_id: int
    rows_count: int
    schema_data: dict[str, Any] = Field(alias="schema_json")
    summary_json: dict[str, Any]
    preview_json: list[dict[str, Any]]
    data_location: str
    created_at: datetime

class NormalizedDatasetDetailRead(NormalizedDatasetRead):
    processing_task: ProcessingTaskShortRead
    report: ReportShortRead