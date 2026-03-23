from __future__ import annotations
from app.db.session import SessionLocal
from app.services.processing_service import ProcessingService
from app.tasks.celery_app import celery_app

@celery_app.task(name="app.tasks.report_tasks.run_processing_task")
def run_processing_task(task_id: int) -> dict[str, object]:
    db = SessionLocal()
    try:
        service = ProcessingService(db)
        task = service.run_processing_task_sync(task_id=task_id)
        return {
            "task_id": task.id,
            "status": task.status.value,
            "progress": task.progress,
            "warning_count": task.warning_count,
            "error_count": task.error_count,
            "quality_score": float(task.quality_score) if task.quality_score is not None else None,
            "error_summary": task.error_summary,
        }
    finally:
        db.close()
