from __future__ import annotations
from pydantic import Field
from app.models.enums import RoleCodeEnum
from .common import BaseSchema, IdSchema, TimestampSchema

class RoleCreate(BaseSchema):
    code: RoleCodeEnum
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None

class RoleUpdate(BaseSchema):
    code: RoleCodeEnum | None = None
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = None

class RoleShortRead(IdSchema):
    code: RoleCodeEnum
    name: str

class RoleRead(TimestampSchema, IdSchema):
    code: RoleCodeEnum
    name: str
    description: str | None = None