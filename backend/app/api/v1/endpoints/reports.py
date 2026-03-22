from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db, require_operator_user
from app.models.ml_template import MlTemplate
from app.models.project import Project
from app.models.report import Report
from app.models.report_type import ReportType
from app.models.report_upload import ReportUpload
from app.models.user import User
from app.schemas.report import (
    ReportCreate,
    ReportDetailRead,
    ReportRead,
    ReportStatusUpdate,
    ReportUpdate,
)
from app.schemas.upload import ReportUploadDetailRead
from app.services.upload_service import UploadService

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def _get_report_detail_or_404(db: Session, report_id: int) -> Report:
    stmt = (
        select(Report)
        .options(
            selectinload(Report.report_type),
            selectinload(Report.creator),
            selectinload(Report.current_assignee),
            selectinload(Report.approver),
            selectinload(Report.ml_template),
        )
        .where(Report.id == report_id)
    )
    report = db.scalar(stmt)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


@router.get("/", response_model=list[ReportRead])
def list_reports(db: Session = Depends(get_db)) -> list[Report]:
    stmt = select(Report).order_by(Report.id)
    return list(db.scalars(stmt).all())


@router.get("/{report_id}", response_model=ReportDetailRead)
def get_report(report_id: int, db: Session = Depends(get_db)) -> Report:
    return _get_report_detail_or_404(db, report_id)


@router.post("/", response_model=ReportDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_operator_user)])
def create_report(payload: ReportCreate, db: Session = Depends(get_db)) -> Report:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    report_type = db.get(ReportType, payload.report_type_id)
    if report_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")

    creator = db.get(User, payload.creator_id)
    if creator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator user not found.")

    if payload.current_assignee_id is not None:
        assignee = db.get(User, payload.current_assignee_id)
        if assignee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found.")

    if payload.approver_id is not None:
        approver = db.get(User, payload.approver_id)
        if approver is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver user not found.")

    if payload.ml_template_id is not None:
        template = db.get(MlTemplate, payload.ml_template_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ML template not found.")

    report = Report(**payload.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post(
    "/{report_id}/uploads/file",
    response_model=ReportUploadDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operator_user)],
)
def upload_report_file(
    report_id: int,
    file: UploadFile = File(...),
    comment: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = UploadService(db)
    upload = service.create_report_upload(
        report_id=report_id,
        upload_file=file,
        uploaded_by=current_user,
        comment=comment,
    )
    stmt = (
        select(ReportUpload)
        .options(
            selectinload(ReportUpload.report),
            selectinload(ReportUpload.report_type),
            selectinload(ReportUpload.uploader),
        )
        .where(ReportUpload.id == upload.id)
    )
    return db.scalar(stmt)


@router.patch("/{report_id}", response_model=ReportDetailRead, dependencies=[Depends(require_operator_user)])
def update_report(report_id: int, payload: ReportUpdate, db: Session = Depends(get_db)) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    data = payload.model_dump(exclude_unset=True)

    if "report_type_id" in data and data["report_type_id"] is not None:
        report_type = db.get(ReportType, data["report_type_id"])
        if report_type is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")

    if "current_assignee_id" in data and data["current_assignee_id"] is not None:
        assignee = db.get(User, data["current_assignee_id"])
        if assignee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found.")

    if "approver_id" in data and data["approver_id"] is not None:
        approver = db.get(User, data["approver_id"])
        if approver is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver user not found.")

    if "ml_template_id" in data and data["ml_template_id"] is not None:
        template = db.get(MlTemplate, data["ml_template_id"])
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ML template not found.")

    for field, value in data.items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.patch("/{report_id}/status", response_model=ReportDetailRead, dependencies=[Depends(require_operator_user)])
def update_report_status(
    report_id: int,
    payload: ReportStatusUpdate,
    db: Session = Depends(get_db),
) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if payload.current_assignee_id is not None:
        assignee = db.get(User, payload.current_assignee_id)
        if assignee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found.")

    if payload.approver_id is not None:
        approver = db.get(User, payload.approver_id)
        if approver is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver user not found.")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)
