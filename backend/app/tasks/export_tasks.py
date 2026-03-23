from __future__ import annotations
from app.tasks.celery_app import celery_app

@celery_app.task(name="app.tasks.export_tasks.ping")
def ping() -> str:
    return "pong"
