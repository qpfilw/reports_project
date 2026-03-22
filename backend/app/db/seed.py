from __future__ import annotations
from dataclasses import dataclass
from typing import Final
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.enums import RoleCodeEnum
from app.models.role import Role
from app.models.user import User


@dataclass(frozen=True)
class RolePreset:
    code: RoleCodeEnum
    name: str
    description: str


ROLE_PRESETS: Final[list[RolePreset]] = [
    RolePreset(
        code=RoleCodeEnum.ADMIN,
        name="Администратор",
        description="Полный доступ к управлению системой",
    ),
    RolePreset(
        code=RoleCodeEnum.MANAGER,
        name="Менеджер",
        description="Управление проектами, отчетами, задачами обработки и составление аналитических визуализаций",
    ),
    RolePreset(
        code=RoleCodeEnum.OPERATOR,
        name="Оператор",
        description="Загрузка файлов, запуск обработки, возможность редактирования и чтения",
    ),
    RolePreset(
        code=RoleCodeEnum.VIEWER,
        name="Наблюдатель",
        description="Просмотр данных и результатов без возможности вносить изменения",
    ),
]

def seed_roles(db: Session) -> list[Role]:
    existing_roles = {
        role.code: role
        for role in db.scalars(select(Role)).all()
    }

    created_or_existing: list[Role] = []

    for preset in ROLE_PRESETS:
        role = existing_roles.get(preset.code)
        if role is None:
            role = Role(
                code=preset.code,
                name=preset.name,
                description=preset.description,
            )
            db.add(role)
            db.flush()
        created_or_existing.append(role)

    db.commit()
    return created_or_existing


def get_role_by_code(db: Session, code: RoleCodeEnum) -> Role | None:
    return db.scalar(select(Role).where(Role.code == code))

def get_user_by_email(db: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    return db.scalar(select(User).where(User.email == normalized_email))

def admin_exists(db: Session) -> bool:
    stmt = (
        select(User.id)
        .join(Role, Role.id == User.role_id)
        .where(Role.code == RoleCodeEnum.ADMIN)
        .limit(1)
    )
    return db.scalar(stmt) is not None

def create_admin_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    position: str | None = None,
    department: str | None = None,
    is_active: bool = True,
    is_blocked: bool = False,
) -> User:
    normalized_email = email.strip().lower()

    if not normalized_email:
        raise ValueError("Admin email is required.")
    if not password or len(password) < 8:
        raise ValueError("Admin password must contain at least 8 characters.")
    if not full_name.strip():
        raise ValueError("Admin full_name is required.")

    existing_user = get_user_by_email(db, normalized_email)
    if existing_user is not None:
        raise ValueError(f"User with email '{normalized_email}' already exists.")

    admin_role = get_role_by_code(db, RoleCodeEnum.ADMIN)
    if admin_role is None:
        raise ValueError("ADMIN role not found. Seed roles first.")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        position=position.strip() if position else None,
        department=department.strip() if department else None,
        is_active=is_active,
        is_blocked=is_blocked,
        role_id=admin_role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user