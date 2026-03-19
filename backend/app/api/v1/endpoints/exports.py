from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db, require_operator_user
from app.models.dashboard import Dashboard
from app.models.export_artifact import ExportArtifact
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.models.user import User
from app.schemas.export import ExportArtifactCreate, ExportArtifactDetailRead, ExportArtifactRead

router = APIRouter(dependencies=[Depends(get_current_active_user)])

def _get_export_detail_or_404(db: Session, export_id: int) -> ExportArtifact:
    stmt = (
        select(ExportArtifact)
        .options(
            selectinload(ExportArtifact.processing_task),
            selectinload(ExportArtifact.report),
            selectinload(ExportArtifact.dashboard),
            selectinload(ExportArtifact.creator),
        )
        .where(ExportArtifact.id == export_id)
    )
    export = db.scalar(stmt)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export artifact not found.")
    return export

@router.get("/", response_model=list[ExportArtifactRead])
def list_exports(db: Session = Depends(get_db)) -> list[ExportArtifact]:
    stmt = select(ExportArtifact).order_by(ExportArtifact.id.desc())
    return list(db.scalars(stmt).all())

@router.get("/{export_id}", response_model=ExportArtifactDetailRead)
def get_export(export_id: int, db: Session = Depends(get_db)) -> ExportArtifact:
    return _get_export_detail_or_404(db, export_id)

@router.post("/", response_model=ExportArtifactDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_operator_user)])
def create_export(payload: ExportArtifactCreate, db: Session = Depends(get_db)) -> ExportArtifact:
    if payload.processing_task_id is not None:
        task = db.get(ProcessingTask, payload.processing_task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    if payload.report_id is not None:
        report = db.get(Report, payload.report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if payload.dashboard_id is not None:
        dashboard = db.get(Dashboard, payload.dashboard_id)
        if dashboard is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")

    if payload.created_by is not None:
        creator = db.get(User, payload.created_by)
        if creator is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator user not found.")

    existing = db.scalar(select(ExportArtifact).where(ExportArtifact.storage_path == payload.storage_path))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Export artifact with this storage path already exists.",
        )

    export = ExportArtifact(**payload.model_dump())
    db.add(export)
    db.commit()
    db.refresh(export)
    return _get_export_detail_or_404(db, export.id)