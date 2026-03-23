from __future__ import annotations
from pydantic import Field
from .common import BaseSchema
from .user import UserDetailRead


class LoginRequest(BaseSchema):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)


class TokenPair(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class ChangePasswordRequest(BaseSchema):
    current_password: str = Field(..., min_length=8, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=255)


class RegisterRequest(BaseSchema):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    full_name: str = Field(..., min_length=2, max_length=255)
    position: str | None = Field(None, max_length=150)
    department: str | None = Field(None, max_length=150)


class AuthResponse(BaseSchema):
    user: UserDetailRead
    tokens: TokenPair