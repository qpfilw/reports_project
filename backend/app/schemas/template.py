from __future__ import annotations
from typing import Any
from pydantic import Field
from app.models.enums import TemplateTypeEnum
from .common import BaseSchema, IdSchema, TimestampSchema
from .user import UserShortRead

class MlTemplateCreate(BaseSchema):
    code: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    template_type: TemplateTypeEnum
    target_report_type_id: int | None = None
    department: str | None = Field(None, max_length=150)
    config_json: dict[str, Any] = Field(default_factory=dict)
    metrics_json: dict[str, Any] = Field(default_factory=dict)
    model_path: str | None = Field(None, max_length=512)
    version: str = Field(default="1.0", max_length=50)
    is_default: bool = False
    is_active: bool = True
    created_by: int | None = None

class MlTemplateUpdate(BaseSchema):
    code: str | None = Field(None, min_length=2, max_length=100)
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    template_type: TemplateTypeEnum | None = None
    target_report_type_id: int | None = None
    department: str | None = Field(None, max_length=150)
    config_json: dict[str, Any] | None = None
    metrics_json: dict[str, Any] | None = None
    model_path: str | None = Field(None, max_length=512)
    version: str | None = Field(None, max_length=50)
    is_default: bool | None = None
    is_active: bool | None = None

class MlTemplateShortRead(IdSchema):
    code: str
    name: str
    template_type: TemplateTypeEnum
    version: str
    is_default: bool
    is_active: bool
    target_report_type_id: int | None = None

class MlTemplateRead(TimestampSchema, IdSchema):
    code: str
    name: str
    description: str | None = None
    template_type: TemplateTypeEnum
    target_report_type_id: int | None = None
    department: str | None = None
    config_json: dict[str, Any]
    metrics_json: dict[str, Any]
    model_path: str | None = None
    version: str
    is_default: bool
    is_active: bool
    created_by: int | None = None

class MlTemplateDetailRead(MlTemplateRead):
    creator: UserShortRead | None = None