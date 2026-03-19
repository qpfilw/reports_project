from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_db, require_admin_user
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.user import User
from app.schemas.audit import AuditLogCreate, AuditLogDetailRead, AuditLogRead

router = APIRouter(dependencies=[Depends(require_admin_user)])

def _get_audit_log_detail_or_404(db: Session, audit_id: int) -> AuditLog:
    stmt = (
        select(AuditLog)
        .options(
            selectinload(AuditLog.user),
            selectinload(AuditLog.project),
        )
        .where(AuditLog.id == audit_id)
    )
    audit_log = db.scalar(stmt)
    if audit_log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found.")
    return audit_log

@router.get("/", response_model=list[AuditLogRead])
def list_audit_logs(db: Session = Depends(get_db)) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    return list(db.scalars(stmt).all())

@router.get("/{audit_id}", response_model=AuditLogDetailRead)
def get_audit_log(audit_id: int, db: Session = Depends(get_db)) -> AuditLog:
    return _get_audit_log_detail_or_404(db, audit_id)

@router.get("/users/{user_id}", response_model=list[AuditLogRead])
def list_user_audit_logs(user_id: int, db: Session = Depends(get_db)) -> list[AuditLog]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    stmt = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.id.desc())
    )
    return list(db.scalars(stmt).all())

@router.get("/projects/{project_id}", response_model=list[AuditLogRead])
def list_project_audit_logs(project_id: int, db: Session = Depends(get_db)) -> list[AuditLog]:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    stmt = (
        select(AuditLog)
        .where(AuditLog.project_id == project_id)
        .order_by(AuditLog.id.desc())
    )
    return list(db.scalars(stmt).all())

@router.post("/", response_model=AuditLogDetailRead, status_code=status.HTTP_201_CREATED)
def create_audit_log(payload: AuditLogCreate, db: Session = Depends(get_db)) -> AuditLog:
    if payload.user_id is not None:
        user = db.get(User, payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.project_id is not None:
        project = db.get(Project, payload.project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    audit_log = AuditLog(**payload.model_dump())
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return _get_audit_log_detail_or_404(db, audit_log.id)