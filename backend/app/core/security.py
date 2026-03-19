from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenDecodeError(Exception):
    pass

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def _build_token(
    *,
    subject: str,
    token_type: str,
    secret_key: str,
    expires_delta: timedelta,
    extra_payload: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra_payload:
        payload.update(extra_payload)

    return jwt.encode(payload, secret_key, algorithm=settings.jwt_algorithm)

def create_access_token(user_id: int, role_code: str | None = None) -> str:
    extra = {"role": role_code} if role_code else None
    return _build_token(
        subject=str(user_id),
        token_type="access",
        secret_key=settings.jwt_secret_key,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_payload=extra,
    )

def create_refresh_token(user_id: int) -> str:
    return _build_token(
        subject=str(user_id),
        token_type="refresh",
        secret_key=settings.jwt_refresh_secret_key,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )

def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except (ExpiredSignatureError, InvalidTokenError) as exc:
        raise TokenDecodeError(str(exc)) from exc

    if payload.get("type") != "access":
        raise TokenDecodeError("Invalid token type.")

    return payload

def decode_refresh_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_refresh_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except (ExpiredSignatureError, InvalidTokenError) as exc:
        raise TokenDecodeError(str(exc)) from exc

    if payload.get("type") != "refresh":
        raise TokenDecodeError("Invalid token type.")

    return payload