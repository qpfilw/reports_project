from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db, require_operator_user
from app.models.enums import ProcessingStatusEnum
from app.models.processing_log import ProcessingLog
from app.models.processing_task import ProcessingTask
from app.models.task_error import TaskError
from app.models.user import User
from app.schemas.processing import (
    ProcessingLogCreate,
    ProcessingLogRead,
    ProcessingTaskDetailRead,
    ProcessingTaskLaunchRequest,
    ProcessingTaskRead,
    ProcessingTaskUpdate,
    TaskErrorCreate,
    TaskErrorRead,
)
from app.services.processing_service import ProcessingService

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def _get_task_detail_or_404(db: Session, task_id: int) -> ProcessingTask:
    stmt = (
        select(ProcessingTask)
        .options(
            selectinload(ProcessingTask.report),
            selectinload(ProcessingTask.report_upload),
            selectinload(ProcessingTask.ml_template),
            selectinload(ProcessingTask.creator),
            selectinload(ProcessingTask.logs),
            selectinload(ProcessingTask.errors),
            selectinload(ProcessingTask.normalized_dataset),
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")
    return task


@router.get("/tasks", response_model=list[ProcessingTaskRead])
def list_processing_tasks(db: Session = Depends(get_db)) -> list[ProcessingTask]:
    stmt = select(ProcessingTask).order_by(ProcessingTask.id.desc())
    return list(db.scalars(stmt).all())


@router.get("/tasks/{task_id}", response_model=ProcessingTaskDetailRead)
def get_processing_task(task_id: int, db: Session = Depends(get_db)) -> ProcessingTask:
    return _get_task_detail_or_404(db, task_id)


@router.post(
    "/tasks",
    response_model=ProcessingTaskDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operator_user)],
)
def create_processing_task(
    payload: ProcessingTaskLaunchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProcessingTask:
    service = ProcessingService(db)
    task = service.launch_processing_task(
        report_id=payload.report_id,
        report_upload_id=payload.report_upload_id,
        ml_template_id=payload.ml_template_id,
        created_by=current_user,
        priority=payload.priority,
        params_json=payload.params_json,
    )
    service.dispatch_processing_task(task_id=task.id)
    return _get_task_detail_or_404(db, task.id)


@router.post(
    "/tasks/{task_id}/dispatch",
    response_model=ProcessingTaskDetailRead,
    dependencies=[Depends(require_operator_user)],
)
def dispatch_existing_processing_task(task_id: int, db: Session = Depends(get_db)) -> ProcessingTask:
    service = ProcessingService(db)
    service.dispatch_processing_task(task_id=task_id)
    return _get_task_detail_or_404(db, task_id)


@router.patch("/tasks/{task_id}", response_model=ProcessingTaskDetailRead, dependencies=[Depends(require_operator_user)])
def update_processing_task(
    task_id: int,
    payload: ProcessingTaskUpdate,
    db: Session = Depends(get_db),
) -> ProcessingTask:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return _get_task_detail_or_404(db, task.id)


@router.get("/tasks/{task_id}/logs", response_model=list[ProcessingLogRead])
def list_processing_logs(task_id: int, db: Session = Depends(get_db)) -> list[ProcessingLog]:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    stmt = select(ProcessingLog).where(ProcessingLog.processing_task_id == task_id).order_by(ProcessingLog.id)
    return list(db.scalars(stmt).all())


@router.post(
    "/tasks/{task_id}/logs",
    response_model=ProcessingLogRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operator_user)],
)
def create_processing_log(
    task_id: int,
    payload: ProcessingLogCreate,
    db: Session = Depends(get_db),
) -> ProcessingLog:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    if payload.processing_task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="processing_task_id in payload must match path parameter.",
        )

    log = ProcessingLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/tasks/{task_id}/errors", response_model=list[TaskErrorRead])
def list_task_errors(task_id: int, db: Session = Depends(get_db)) -> list[TaskError]:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    stmt = select(TaskError).where(TaskError.processing_task_id == task_id).order_by(TaskError.id)
    return list(db.scalars(stmt).all())


@router.post(
    "/tasks/{task_id}/errors",
    response_model=TaskErrorRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operator_user)],
)
def create_task_error(
    task_id: int,
    payload: TaskErrorCreate,
    db: Session = Depends(get_db),
) -> TaskError:
    task = db.get(ProcessingTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    if payload.processing_task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="processing_task_id in payload must match path parameter.",
        )

    error = TaskError(**payload.model_dump())
    db.add(error)

    task.error_count = (task.error_count or 0) + 1
    if payload.is_critical and task.error_summary is None:
        task.error_summary = payload.details or payload.error_code

    db.commit()
    db.refresh(error)
    return error


@router.get("/summary")
def processing_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    total = db.scalar(select(func.count()).select_from(ProcessingTask)) or 0
    queued = db.scalar(
        select(func.count()).select_from(ProcessingTask).where(ProcessingTask.status == ProcessingStatusEnum.QUEUED)
    ) or 0
    running = db.scalar(
        select(func.count()).select_from(ProcessingTask).where(ProcessingTask.status == ProcessingStatusEnum.RUNNING)
    ) or 0
    success = db.scalar(
        select(func.count()).select_from(ProcessingTask).where(ProcessingTask.status == ProcessingStatusEnum.SUCCESS)
    ) or 0
    failed = db.scalar(
        select(func.count()).select_from(ProcessingTask).where(ProcessingTask.status == ProcessingStatusEnum.FAILED)
    ) or 0

    return {
        "total": total,
        "queued": queued,
        "running": running,
        "success": success,
        "failed": failed,
    }
