from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin_user
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(dependencies=[Depends(require_admin_user)])

@router.get("/", response_model=list[RoleRead])
def list_roles(db: Session = Depends(get_db)) -> list[Role]:
    stmt = select(Role).order_by(Role.id)
    return list(db.scalars(stmt).all())

@router.get("/{role_id}", response_model=RoleRead)
def get_role(role_id: int, db: Session = Depends(get_db)) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return role

@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)) -> Role:
    existing_by_code = db.scalar(select(Role).where(Role.code == payload.code))
    if existing_by_code is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists.")

    existing_by_name = db.scalar(select(Role).where(Role.name == payload.name))
    if existing_by_name is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists.")

    role = Role(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.patch("/{role_id}", response_model=RoleRead)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db)) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    data = payload.model_dump(exclude_unset=True)

    if "code" in data:
        existing = db.scalar(select(Role).where(Role.code == data["code"], Role.id != role_id))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role code already exists.")

    if "name" in data:
        existing = db.scalar(select(Role).where(Role.name == data["name"], Role.id != role_id))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists.")

    for field, value in data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)
    return role