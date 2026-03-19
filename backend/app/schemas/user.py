from __future__ import annotations
from datetime import datetime
from pydantic import Field
from .common import BaseSchema, IdSchema, TimestampSchema
from .role import RoleShortRead

class UserCreate(BaseSchema):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    full_name: str = Field(..., min_length=2, max_length=255)
    position: str | None = Field(None, max_length=150)
    department: str | None = Field(None, max_length=150)
    role_id: int

class UserUpdate(BaseSchema):
    email: str | None = Field(None, min_length=5, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=255)
    full_name: str | None = Field(None, min_length=2, max_length=255)
    position: str | None = Field(None, max_length=150)
    department: str | None = Field(None, max_length=150)
    is_active: bool | None = None
    is_blocked: bool | None = None
    role_id: int | None = None

class UserShortRead(IdSchema):
    email: str
    full_name: str
    position: str | None = None
    department: str | None = None
    is_active: bool

class UserRead(TimestampSchema, IdSchema):
    email: str
    full_name: str
    position: str | None = None
    department: str | None = None
    is_active: bool
    is_blocked: bool
    last_login_at: datetime | None = None
    role_id: int

class UserDetailRead(UserRead):
    role: RoleShortRead