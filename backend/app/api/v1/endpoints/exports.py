from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_approved_user, get_db, require_operator_user
from app.core.access import apply_project_scope, ensure_project_read_access, ensure_project_write_access
from app.models.dashboard import Dashboard
from app.models.export_artifact import ExportArtifact
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.models.user import User
from app.schemas.export import ExportArtifactCreate, ExportArtifactDetailRead, ExportArtifactRead, ExportRequest
from app.services.export_service import ExportService
from app.utils.storage import resolve_storage_path

router = APIRouter(dependencies=[Depends(require_approved_user)])


def _get_export_detail_or_404(db: Session, export_id: int) -> ExportArtifact:
    stmt = (
        select(ExportArtifact)
        .options(
            selectinload(ExportArtifact.processing_task).selectinload(ProcessingTask.report),
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


def _resolve_export_project_id(export: ExportArtifact) -> int | None:
    if export.report is not None:
        return export.report.project_id
    if export.processing_task is not None and export.processing_task.report is not None:
        return export.processing_task.report.project_id
    if export.dashboard is not None:
        return export.dashboard.project_id
    return None


@router.get("/", response_model=list[ExportArtifactRead])
def list_exports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[ExportArtifact]:
    stmt = (
        select(ExportArtifact)
        .options(
            selectinload(ExportArtifact.processing_task).selectinload(ProcessingTask.report),
            selectinload(ExportArtifact.report),
            selectinload(ExportArtifact.dashboard),
        )
        .outerjoin(ProcessingTask, ExportArtifact.processing_task_id == ProcessingTask.id)
        .outerjoin(Report, or_(ExportArtifact.report_id == Report.id, ProcessingTask.report_id == Report.id))
        .order_by(ExportArtifact.id.desc())
    )
    stmt = apply_project_scope(stmt, project_column=Report.project_id, current_user=current_user)
    stmt = stmt.distinct(ExportArtifact.id)
    return list(db.scalars(stmt).all())


@router.get("/{export_id}", response_model=ExportArtifactDetailRead)
def get_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> ExportArtifact:
    export = _get_export_detail_or_404(db, export_id)
    project_id = _resolve_export_project_id(export)
    if project_id is not None:
        ensure_project_read_access(db, project_id=project_id, current_user=current_user)
    return export


@router.get("/{export_id}/download")
def download_export(
    export_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> FileResponse:
    export = _get_export_detail_or_404(db, export_id)
    project_id = _resolve_export_project_id(export)
    if project_id is not None:
        ensure_project_read_access(db, project_id=project_id, current_user=current_user)

    file_path = resolve_storage_path(export.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored export file not found.")

    format_value = getattr(export.format, "value", export.format)
    media_type = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
    }.get(str(format_value), "application/octet-stream")
    return FileResponse(path=file_path, media_type=media_type, filename=file_path.name)


@router.post(
    "/run",
    response_model=ExportArtifactDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operator_user)],
)
def run_export(
    payload: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> ExportArtifact:
    if payload.processing_task_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="processing_task_id is required for result export.",
        )

    task = db.get(ProcessingTask, payload.processing_task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")
    report = db.get(Report, task.report_id)
    ensure_project_write_access(db, project_id=report.project_id, current_user=current_user)

    service = ExportService(db)
    artifact = service.export_processing_result(
        processing_task_id=payload.processing_task_id,
        export_format=payload.format,
        created_by=current_user,
    )
    return _get_export_detail_or_404(db, artifact.id)


@router.post("/", response_model=ExportArtifactDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_operator_user)])
def create_export(
    payload: ExportArtifactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> ExportArtifact:
    project_id: int | None = None

    linked_task = None
    linked_report = None
    linked_dashboard = None

    if payload.processing_task_id is not None:
        linked_task = db.get(ProcessingTask, payload.processing_task_id)
        if linked_task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")
        linked_report = db.get(Report, linked_task.report_id)
        if linked_report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked report not found for processing task.")
        project_id = linked_report.project_id

    if payload.report_id is not None:
        report = db.get(Report, payload.report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        if project_id is not None and report.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report does not match the selected processing task project.")
        linked_report = report
        project_id = report.project_id

    if payload.dashboard_id is not None:
        dashboard = db.get(Dashboard, payload.dashboard_id)
        if dashboard is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
        if project_id is not None and dashboard.project_id != project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dashboard does not belong to the selected project.")
        linked_dashboard = dashboard
        project_id = dashboard.project_id

    if project_id is not None:
        ensure_project_write_access(db, project_id=project_id, current_user=current_user)

    if payload.created_by is not None and payload.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can create exports only on your own behalf.")

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