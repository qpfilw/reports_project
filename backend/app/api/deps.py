from __future__ import annotations
from collections.abc import Generator
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    AccessDeniedError,
    AuthenticationRequiredError,
    ObjectNotFoundError,
    raise_http,
)
from app.core.permissions import can_manage_admin_panel, can_use_platform, is_admin, is_manager, is_operator, is_pending
from app.core.security import TokenDecodeError, decode_access_token
from app.db.session import get_db as _get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    yield from _get_db()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> User:
    if credentials is None:
        raise_http(
            AuthenticationRequiredError(
                detail="Authentication credentials were not provided.",
                code="AUTH_MISSING_CREDENTIALS",
            )
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (TokenDecodeError, KeyError, ValueError):
        raise_http(
            AuthenticationRequiredError(
                detail="Invalid or expired access token.",
                code="AUTH_INVALID_TOKEN",
            )
        )

    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    user = db.scalar(stmt)
    if user is None:
        raise_http(
            ObjectNotFoundError(
                detail="User not found.",
                code="AUTH_USER_NOT_FOUND",
                status_code=401,
            )
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise_http(
            AccessDeniedError(
                detail="User is inactive.",
                code="USER_INACTIVE",
            )
        )

    if current_user.is_blocked:
        raise_http(
            AccessDeniedError(
                detail="User is blocked.",
                code="USER_BLOCKED",
            )
        )

    return current_user


def require_approved_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not can_use_platform(current_user):
        if is_pending(current_user):
            raise_http(
                AccessDeniedError(
                    detail="Your account is pending approval by an administrator.",
                    code="USER_PENDING_APPROVAL",
                )
            )
        raise_http(
            AccessDeniedError(
                detail="Your account does not have access to the platform.",
                code="USER_PLATFORM_ACCESS_DENIED",
            )
        )
    return current_user


def require_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not can_manage_admin_panel(user=current_user):
        raise_http(
            AccessDeniedError(
                detail="Admin access required.",
                code="ADMIN_ACCESS_REQUIRED",
            )
        )
    return current_user


def require_manager_user(current_user: User = Depends(require_approved_user)) -> User:
    if not (is_admin(current_user) or is_manager(current_user)):
        raise_http(
            AccessDeniedError(
                detail="Manager access required.",
                code="MANAGER_ACCESS_REQUIRED",
            )
        )
    return current_user


def require_operator_user(current_user: User = Depends(require_approved_user)) -> User:
    if not (is_admin(current_user) or is_manager(current_user) or is_operator(current_user)):
        raise_http(
            AccessDeniedError(
                detail="Operator access required.",
                code="OPERATOR_ACCESS_REQUIRED",
            )
        )
    return current_user