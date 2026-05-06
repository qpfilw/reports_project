from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .common import BaseSchema, IdSchema, TimestampSchema
from .user import UserShortRead


class ProcessingScriptBase(BaseSchema):
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    target_report_type_id: int | None = None
    script_code: str = Field(..., min_length=10)
    version: str = Field(default="1.0", max_length=50)
    is_default: bool = False
    is_active: bool = True
    validation_json: dict[str, Any] = Field(default_factory=dict)
    created_by: int | None = None


class ProcessingScriptCreate(ProcessingScriptBase):
    pass


class ProcessingScriptUpdate(BaseSchema):
    code: str | None = Field(None, min_length=2, max_length=100)
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    target_report_type_id: int | None = None
    script_code: str | None = Field(None, min_length=10)
    version: str | None = Field(None, max_length=50)
    is_default: bool | None = None
    is_active: bool | None = None
    validation_json: dict[str, Any] | None = None
    created_by: int | None = None


class ProcessingScriptShortRead(IdSchema):
    code: str
    name: str
    version: str
    target_report_type_id: int | None = None
    is_default: bool
    is_active: bool


class ProcessingScriptRead(TimestampSchema, IdSchema):
    code: str
    name: str
    description: str | None = None
    target_report_type_id: int | None = None
    script_code: str
    version: str
    is_default: bool
    is_active: bool
    validation_json: dict[str, Any]
    created_by: int | None = None


class ProcessingScriptDetailRead(ProcessingScriptRead):
    creator: UserShortRead | None = None


class ProcessingScriptValidateRequest(BaseSchema):
    script_code: str = Field(..., min_length=10)
    sample_context: dict[str, Any] | None = None
    sample_row: dict[str, Any] | None = None


class ProcessingScriptValidateResponse(BaseSchema):
    is_valid: bool
    message: str
    output_row: dict[str, Any] | None = None
    added_columns: list[str] = Field(default_factory=list)
    error: str | None = None
