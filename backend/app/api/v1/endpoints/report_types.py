from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_approved_user, require_manager_user
from app.models.report_type import ReportType
from app.schemas.report import ReportTypeCreate, ReportTypeRead, ReportTypeUpdate

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
def create_report_type(payload: ReportTypeCreate, db: Session = Depends(get_db)) -> ReportType:
    existing = db.scalar(select(ReportType).where(ReportType.code == payload.code))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report type code already exists.")

    report_type = ReportType(**payload.model_dump())
    db.add(report_type)
    db.commit()
    db.refresh(report_type)
    return report_type

@router.patch("/{report_type_id}", response_model=ReportTypeRead, dependencies=[Depends(require_manager_user)])
def update_report_type(report_type_id: int, payload: ReportTypeUpdate, db: Session = Depends(get_db)) -> ReportType:
    report_type = db.get(ReportType, report_type_id)
    if report_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")

    data = payload.model_dump(exclude_unset=True)

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

    db.commit()
    db.refresh(report_type)
    return report_type