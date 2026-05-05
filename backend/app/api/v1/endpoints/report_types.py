from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_approved_user, require_manager_user
from app.models.enums import AuditActionEnum, AuditEntityTypeEnum
from app.models.report_type import ReportType
from app.models.user import User
from app.schemas.report import ReportTypeCreate, ReportTypeRead, ReportTypeUpdate
from app.services.audit_service import log_audit, snapshot_report_type

router = APIRouter(dependencies=[Depends(require_approved_user)])

@router.get("/", response_model=list[ReportTypeRead])
def list_report_types(db: Session = Depends(get_db)) -> list[ReportType]:
    stmt = select(ReportType).order_by(ReportType.id)
    return list(db.scalars(stmt).all())

@router.get("/{report_type_id}", response_model=ReportTypeRead)
def get_report_type(report_type_id: int, db: Session = Depends(get_db)) -> ReportType:
    report_type = db.get(ReportType, report_type_id)
    if report_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")
    return report_type

@router.post("/", response_model=ReportTypeRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager_user)])
def create_report_type(payload: ReportTypeCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_manager_user)) -> ReportType:
    existing = db.scalar(select(ReportType).where(ReportType.code == payload.code))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report type code already exists.")

    report_type = ReportType(**payload.model_dump())
    db.add(report_type)
    db.flush()
    log_audit(db, action=AuditActionEnum.CREATE, entity_type=AuditEntityTypeEnum.TEMPLATE, entity_id=report_type.id, actor=current_user, after_json={"event": "report_type_created", **(snapshot_report_type(report_type) or {})}, request=request)
    db.commit()
    db.refresh(report_type)
    return report_type

@router.patch("/{report_type_id}", response_model=ReportTypeRead, dependencies=[Depends(require_manager_user)])
def update_report_type(report_type_id: int, payload: ReportTypeUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_manager_user)) -> ReportType:
    report_type = db.get(ReportType, report_type_id)
    if report_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")

    data = payload.model_dump(exclude_unset=True)
    before_report_type = snapshot_report_type(report_type)

    if "code" in data:
        existing = db.scalar(
            select(ReportType).where(
                ReportType.code == data["code"],
                ReportType.id != report_type_id,
            )
        )
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report type code already exists.")

    for field, value in data.items():
        setattr(report_type, field, value)

    if data:
        log_audit(db, action=AuditActionEnum.UPDATE, entity_type=AuditEntityTypeEnum.TEMPLATE, entity_id=report_type.id, actor=current_user, before_json=before_report_type, after_json={"event": "report_type_updated", **(snapshot_report_type(report_type) or {})}, request=request)

    db.commit()
    db.refresh(report_type)
    return report_type