from __future__ import annotations
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

broker_url = settings.celery_broker_url or settings.redis_url
result_backend = settings.celery_result_backend or settings.redis_url

celery_app = Celery(
    "enterprise_reporting_platform",
    broker=broker_url,
    backend=result_backend,
    include=[
        "app.tasks.report_tasks",
        "app.tasks.export_tasks",
        "app.tasks.analytics_tasks",
        "app.tasks.maintenance_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_eager_propagates,
    result_expires=3600,
)
