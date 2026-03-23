from __future__ import annotations
from collections.abc import Generator
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.core.access import get_role_code, is_pending
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
        )

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (TokenDecodeError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive.",
        )

    if current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked.",
        )

    return current_user

def require_approved_user(current_user: User = Depends(get_current_active_user)) -> User:
    if is_pending(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval by an administrator.",
        )
    return current_user

def require_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if get_role_code(current_user) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user

def require_manager_user(current_user: User = Depends(require_approved_user)) -> User:
    if get_role_code(current_user) not in {"admin", "manager"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required.",
        )
    return current_user

def require_operator_user(current_user: User = Depends(require_approved_user)) -> User:
    if get_role_code(current_user) not in {"admin", "manager", "operator"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator access required.",
        )
    return current_user