from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_active_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.enums import RoleCodeEnum
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenPair,
)
from app.schemas.user import UserDetailRead

router = APIRouter()

def _get_user_detail_or_404(db: Session, user_id: int) -> User:
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user

def _issue_tokens(user: User) -> TokenPair:
    role_code = user.role.code.value if hasattr(user.role.code, "value") else str(user.role.code)
    return TokenPair(
        access_token=create_access_token(user.id, role_code=role_code),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
    )

def _get_default_registration_role(db: Session) -> Role:
    preferred_order = [
        RoleCodeEnum.VIEWER,
        RoleCodeEnum.OPERATOR,
        RoleCodeEnum.MANAGER,
    ]

    stmt = (
        select(Role)
        .where(Role.code.in_(preferred_order))
        .order_by(
            case(
                (Role.code == RoleCodeEnum.VIEWER, 1),
                (Role.code == RoleCodeEnum.OPERATOR, 2),
                (Role.code == RoleCodeEnum.MANAGER, 3),
                else_=99,
            )
        )
    )
    role = db.scalar(stmt)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No safe default role exists. Create VIEWER or OPERATOR role first.",
        )
    return role

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )

    if payload.role_id is not None:
        role = db.get(Role, payload.role_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found.",
            )
        if role.code == RoleCodeEnum.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration with ADMIN role is not allowed.",
            )
    else:
        role = _get_default_registration_role(db)

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        position=payload.position,
        department=payload.department,
        role_id=role.id,
        is_active=True,
        is_blocked=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    user = _get_user_detail_or_404(db, user.id)
    tokens = _issue_tokens(user)
    return AuthResponse(user=UserDetailRead.model_validate(user), tokens=tokens)

@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.email == payload.email)
    )
    user = db.scalar(stmt)

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive.",
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked.",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    tokens = _issue_tokens(user)
    return AuthResponse(user=UserDetailRead.model_validate(user), tokens=tokens)

@router.post("/refresh", response_model=TokenPair)
def refresh_tokens(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        token_payload = decode_refresh_token(payload.refresh_token)
        user_id = int(token_payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user = _get_user_detail_or_404(db, user_id)

    if not user.is_active or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not allowed to obtain tokens.",
        )

    return _issue_tokens(user)

@router.get("/me", response_model=UserDetailRead)
def get_me(current_user: User = Depends(get_current_active_user)) -> UserDetailRead:
    return UserDetailRead.model_validate(current_user)

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "Password changed successfully."}