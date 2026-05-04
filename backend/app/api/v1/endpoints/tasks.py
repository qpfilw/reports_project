from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_approved_user, get_db, require_operator_user
from app.core.access import apply_project_scope, ensure_project_read_access, ensure_project_write_access
from app.models.enums import AuditActionEnum, AuditEntityTypeEnum, ProcessingLogLevelEnum, ProcessingStatusEnum
from app.models.processing_log import ProcessingLog
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.schemas.processing import ProcessingTaskDetailRead, ProcessingTaskRead
from app.schemas.task import TaskProgressResponse, TaskQueueInfo
from app.services.audit_service import write_audit_log

router = APIRouter(dependencies=[Depends(require_approved_user)])


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
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


@router.get("/", response_model=list[ProcessingTaskRead])
def list_tasks(
    report_id: int | None = Query(default=None),
    report_upload_id: int | None = Query(default=None),
    ml_template_id: int | None = Query(default=None),
    created_by: int | None = Query(default=None),
    status_filter: ProcessingStatusEnum | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user=Depends(require_approved_user),
) -> list[ProcessingTask]:
    stmt = select(ProcessingTask).join(Report, ProcessingTask.report_id == Report.id)
    stmt = apply_project_scope(stmt, project_column=Report.project_id, current_user=current_user)

    if report_id is not None:
        stmt = stmt.where(ProcessingTask.report_id == report_id)
    if report_upload_id is not None:
        stmt = stmt.where(ProcessingTask.report_upload_id == report_upload_id)
    if ml_template_id is not None:
        stmt = stmt.where(ProcessingTask.ml_template_id == ml_template_id)
    if created_by is not None:
        stmt = stmt.where(ProcessingTask.created_by == created_by)
    if status_filter is not None:
        stmt = stmt.where(ProcessingTask.status == status_filter)

    stmt = stmt.order_by(ProcessingTask.id.desc())
    return list(db.scalars(stmt).all())


@router.get("/queue-info", response_model=TaskQueueInfo)
def get_queue_info(
    db: Session = Depends(get_db),
    current_user=Depends(require_approved_user),
) -> TaskQueueInfo:
    stmt = select(ProcessingTask).join(Report, ProcessingTask.report_id == Report.id)
    stmt = apply_project_scope(stmt, project_column=Report.project_id, current_user=current_user)
    subquery = stmt.subquery()

    queued = db.scalar(select(func.count()).select_from(subquery).where(subquery.c.status == ProcessingStatusEnum.QUEUED.value)) or 0
    running = db.scalar(select(func.count()).select_from(subquery).where(subquery.c.status == ProcessingStatusEnum.RUNNING.value)) or 0
    failed = db.scalar(select(func.count()).select_from(subquery).where(subquery.c.status == ProcessingStatusEnum.FAILED.value)) or 0
    success = db.scalar(select(func.count()).select_from(subquery).where(subquery.c.status == ProcessingStatusEnum.SUCCESS.value)) or 0

    return TaskQueueInfo(queued=queued, running=running, failed=failed, success=success)


@router.get("/{task_id}/progress", response_model=TaskProgressResponse)
def get_task_progress(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_approved_user),
) -> TaskProgressResponse:
    task = _get_task_detail_or_404(db, task_id)
    ensure_project_read_access(db, project_id=task.report.project_id, current_user=current_user)

    return TaskProgressResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        warning_count=task.warning_count,
        error_count=task.error_count,
        started_at=task.started_at,
        finished_at=task.finished_at,
        error_summary=task.error_summary,
    )


@router.post("/{task_id}/retry", response_model=ProcessingTaskDetailRead, dependencies=[Depends(require_operator_user)])
def retry_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_operator_user),
) -> ProcessingTask:
    task = _get_task_detail_or_404(db, task_id)
    ensure_project_write_access(db, project_id=task.report.project_id, current_user=current_user)

    task.status = ProcessingStatusEnum.RETRY
    task.progress = 0
    task.retry_count = (task.retry_count or 0) + 1
    task.error_summary = None
    task.started_at = None
    task.finished_at = None

    log = ProcessingLog(
        processing_task_id=task.id,
        level=ProcessingLogLevelEnum.INFO,
        stage="retry",
        message="Task marked for retry.",
        context_json={"retry_count": task.retry_count},
    )
    db.add(log)
    write_audit_log(
        db,
        action=AuditActionEnum.PROCESS_RETRY,
        entity_type=AuditEntityTypeEnum.TASK,
        entity_id=task.id,
        user_id=current_user.id,
        project_id=task.report.project_id,
        after_json={"status": task.status, "retry_count": task.retry_count},
        request=request,
    )

    db.commit()
    db.refresh(task)
    return _get_task_detail_or_404(db, task.id)


@router.post("/{task_id}/cancel", response_model=ProcessingTaskDetailRead, dependencies=[Depends(require_operator_user)])
def cancel_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_operator_user),
) -> ProcessingTask:
    task = _get_task_detail_or_404(db, task_id)
    ensure_project_write_access(db, project_id=task.report.project_id, current_user=current_user)

    if task.status in {ProcessingStatusEnum.SUCCESS, ProcessingStatusEnum.FAILED, ProcessingStatusEnum.CANCELLED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled in its current state.",
        )

    task.status = ProcessingStatusEnum.CANCELLED

    log = ProcessingLog(
        processing_task_id=task.id,
        level=ProcessingLogLevelEnum.INFO,
        stage="cancel",
        message="Task cancelled.",
        context_json={},
    )
    db.add(log)
    write_audit_log(
        db,
        action=AuditActionEnum.UPDATE,
        entity_type=AuditEntityTypeEnum.TASK,
        entity_id=task.id,
        user_id=current_user.id,
        project_id=task.report.project_id,
        after_json={"status": task.status},
        request=request,
    )

    db.commit()
    db.refresh(task)
    return _get_task_detail_or_404(db, task.id)
