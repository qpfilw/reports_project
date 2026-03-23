from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_approved_user, get_db, require_operator_user
from app.core.access import apply_project_scope, ensure_project_read_access, ensure_project_write_access
from app.models.normalized_dataset import NormalizedDataset
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.models.user import User
from app.schemas.result import (
    NormalizedDatasetCreate,
    NormalizedDatasetDetailRead,
    NormalizedDatasetRead,
    NormalizedDatasetUpdate,
)

router = APIRouter(dependencies=[Depends(require_approved_user)])


def _get_result_detail_or_404(db: Session, result_id: int) -> NormalizedDataset:
    stmt = (
        select(NormalizedDataset)
        .options(
            selectinload(NormalizedDataset.processing_task),
            selectinload(NormalizedDataset.report),
        )
        .where(NormalizedDataset.id == result_id)
    )
    result = db.scalar(stmt)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Normalized dataset not found.")
    return result


@router.get("/", response_model=list[NormalizedDatasetRead])
def list_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[NormalizedDataset]:
    stmt = select(NormalizedDataset).join(Report, NormalizedDataset.report_id == Report.id)
    stmt = apply_project_scope(stmt, project_column=Report.project_id, current_user=current_user)
    stmt = stmt.order_by(NormalizedDataset.id.desc())
    return list(db.scalars(stmt).all())


@router.get("/by-task/{task_id}", response_model=NormalizedDatasetDetailRead)
def get_result_by_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> NormalizedDataset:
    stmt = (
        select(NormalizedDataset)
        .options(
            selectinload(NormalizedDataset.processing_task),
            selectinload(NormalizedDataset.report),
        )
        .where(NormalizedDataset.processing_task_id == task_id)
    )
    result = db.scalar(stmt)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Normalized dataset not found for this task.")
    ensure_project_read_access(db, project_id=result.report.project_id, current_user=current_user)
    return result


@router.get("/{result_id}", response_model=NormalizedDatasetDetailRead)
def get_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> NormalizedDataset:
    result = _get_result_detail_or_404(db, result_id)
    ensure_project_read_access(db, project_id=result.report.project_id, current_user=current_user)
    return result


@router.post("/", response_model=NormalizedDatasetDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_operator_user)])
def create_result(
    payload: NormalizedDatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> NormalizedDataset:
    task = db.get(ProcessingTask, payload.processing_task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    report = db.get(Report, payload.report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    ensure_project_write_access(db, project_id=report.project_id, current_user=current_user)

    if task.report_id != payload.report_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="processing_task_id does not belong to the specified report.")

    existing = db.scalar(select(NormalizedDataset).where(NormalizedDataset.processing_task_id == payload.processing_task_id))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A normalized dataset for this processing task already exists.",
        )

    result = NormalizedDataset(
        processing_task_id=payload.processing_task_id,
        report_id=payload.report_id,
        rows_count=payload.rows_count,
        schema_json=payload.schema_data,
        summary_json=payload.summary_json,
        preview_json=payload.preview_json,
        data_location=payload.data_location,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return _get_result_detail_or_404(db, result.id)


@router.patch("/{result_id}", response_model=NormalizedDatasetDetailRead, dependencies=[Depends(require_operator_user)])
def update_result(
    result_id: int,
    payload: NormalizedDatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> NormalizedDataset:
    result = db.get(NormalizedDataset, result_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Normalized dataset not found.")
    report = db.get(Report, result.report_id)
    ensure_project_write_access(db, project_id=report.project_id, current_user=current_user)

    data = payload.model_dump(exclude_unset=True)
    if "schema_data" in data:
        data["schema_json"] = data.pop("schema_data")

    for field, value in data.items():
        setattr(result, field, value)

    db.commit()
    db.refresh(result)
    return _get_result_detail_or_404(db, result.id)