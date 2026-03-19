from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_db, require_admin_user
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserDetailRead, UserRead, UserUpdate

router = APIRouter(dependencies=[Depends(require_admin_user)])

def _get_user_detail_or_404(db: Session, user_id: int) -> User:
    stmt = (
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id)
    )
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user

@router.get("/", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    stmt = select(User).order_by(User.id)
    return list(db.scalars(stmt).all())

@router.get("/{user_id}", response_model=UserDetailRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    return _get_user_detail_or_404(db, user_id)

@router.post("/", response_model=UserDetailRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")

    role = db.get(Role, payload.role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        position=payload.position,
        department=payload.department,
        role_id=payload.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _get_user_detail_or_404(db, user.id)

@router.patch("/{user_id}", response_model=UserDetailRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    data = payload.model_dump(exclude_unset=True)

    if "email" in data:
        existing = db.scalar(select(User).where(User.email == data["email"], User.id != user_id))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")

    if "role_id" in data:
        role = db.get(Role, data["role_id"])
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    password = data.pop("password", None)
    if password:
        user.password_hash = hash_password(password)

    for field, value in data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return _get_user_detail_or_404(db, user.id)