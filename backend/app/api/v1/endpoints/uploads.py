from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db, require_operator_user
from app.models.project import Project
from app.models.report import Report
from app.models.report_type import ReportType
from app.models.report_upload import ReportUpload
from app.models.user import User
from app.schemas.upload import (
    ReportUploadCreate,
    ReportUploadDetailRead,
    ReportUploadRead,
    ReportUploadUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_active_user)])

def _get_upload_detail_or_404(db: Session, upload_id: int) -> ReportUpload:
    stmt = (
        select(ReportUpload)
        .options(
            selectinload(ReportUpload.report),
            selectinload(ReportUpload.report_type),
            selectinload(ReportUpload.uploader),
        )
        .where(ReportUpload.id == upload_id)
    )
    upload = db.scalar(stmt)
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")
    return upload

@router.get("/", response_model=list[ReportUploadRead])
def list_uploads(db: Session = Depends(get_db)) -> list[ReportUpload]:
    stmt = select(ReportUpload).order_by(ReportUpload.id)
    return list(db.scalars(stmt).all())

@router.get("/{upload_id}", response_model=ReportUploadDetailRead)
def get_upload(upload_id: int, db: Session = Depends(get_db)) -> ReportUpload:
    return _get_upload_detail_or_404(db, upload_id)

@router.post("/", response_model=ReportUploadDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_operator_user)])
def create_upload(payload: ReportUploadCreate, db: Session = Depends(get_db)) -> ReportUpload:
    report = db.get(Report, payload.report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    report_type = db.get(ReportType, payload.report_type_id)
    if report_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")

    uploader = db.get(User, payload.uploaded_by)
    if uploader is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploader user not found.")

    existing_path = db.scalar(
        select(ReportUpload).where(ReportUpload.storage_path == payload.storage_path)
    )
    if existing_path is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload with this storage path already exists.",
        )

    existing_version = db.scalar(
        select(ReportUpload).where(
            ReportUpload.report_id == payload.report_id,
            ReportUpload.upload_version == payload.upload_version,
        )
    )
    if existing_version is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This upload version already exists for the report.",
        )

    if payload.is_latest:
        stmt = select(ReportUpload).where(
            ReportUpload.report_id == payload.report_id,
            ReportUpload.is_latest.is_(True),
        )
        for old_upload in db.scalars(stmt).all():
            old_upload.is_latest = False

    upload = ReportUpload(**payload.model_dump())
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return _get_upload_detail_or_404(db, upload.id)

@router.get("/{upload_id}/download")
def download_upload(upload_id: int, db: Session = Depends(get_db)) -> FileResponse:
    upload = db.get(ReportUpload, upload_id)
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")

    from app.utils.storage import resolve_storage_path

    file_path = resolve_storage_path(upload.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored upload file not found.")

    media_type = upload.content_type or "application/octet-stream"
    return FileResponse(path=file_path, media_type=media_type, filename=upload.original_filename)

@router.patch("/{upload_id}", response_model=ReportUploadDetailRead, dependencies=[Depends(require_operator_user)])
def update_upload(upload_id: int, payload: ReportUploadUpdate, db: Session = Depends(get_db)) -> ReportUpload:
    upload = db.get(ReportUpload, upload_id)
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")

    data = payload.model_dump(exclude_unset=True)

    if data.get("is_latest") is True:
        stmt = select(ReportUpload).where(
            ReportUpload.report_id == upload.report_id,
            ReportUpload.is_latest.is_(True),
            ReportUpload.id != upload_id,
        )
        for old_upload in db.scalars(stmt).all():
            old_upload.is_latest = False

    for field, value in data.items():
        setattr(upload, field, value)

    db.commit()
    db.refresh(upload)
    return _get_upload_detail_or_404(db, upload.id)