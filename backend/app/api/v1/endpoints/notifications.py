from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db, require_operator_user
from app.models.notification import Notification
from app.models.processing_task import ProcessingTask
from app.models.project import Project
from app.models.report import Report
from app.models.user import User
from app.schemas.notifications import (
    NotificationCreate,
    NotificationDetailRead,
    NotificationRead,
    NotificationUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_active_user)])

def _get_notification_detail_or_404(db: Session, notification_id: int) -> Notification:
    stmt = (
        select(Notification)
        .options(
            selectinload(Notification.user),
            selectinload(Notification.project),
            selectinload(Notification.report),
            selectinload(Notification.processing_task),
        )
        .where(Notification.id == notification_id)
    )
    notification = db.scalar(stmt)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification

@router.get("/", response_model=list[NotificationRead])
def list_notifications(db: Session = Depends(get_db)) -> list[Notification]:
    stmt = select(Notification).order_by(Notification.id.desc())
    return list(db.scalars(stmt).all())

@router.get("/{notification_id}", response_model=NotificationDetailRead)
def get_notification(notification_id: int, db: Session = Depends(get_db)) -> Notification:
    return _get_notification_detail_or_404(db, notification_id)

@router.get("/users/{user_id}", response_model=list[NotificationRead])
def list_user_notifications(user_id: int, db: Session = Depends(get_db)) -> list[Notification]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.id.desc())
    )
    return list(db.scalars(stmt).all())

@router.post("/", response_model=NotificationDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_operator_user)])
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)) -> Notification:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.project_id is not None:
        project = db.get(Project, payload.project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    if payload.report_id is not None:
        report = db.get(Report, payload.report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if payload.processing_task_id is not None:
        task = db.get(ProcessingTask, payload.processing_task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing task not found.")

    notification = Notification(**payload.model_dump())
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return _get_notification_detail_or_404(db, notification.id)

@router.patch("/{notification_id}", response_model=NotificationDetailRead, dependencies=[Depends(require_operator_user)])
def update_notification(
    notification_id: int,
    payload: NotificationUpdate,
    db: Session = Depends(get_db),
) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    data = payload.model_dump(exclude_unset=True)

    if data.get("is_read") is True and "read_at" not in data:
        data["read_at"] = datetime.now(timezone.utc)

    if data.get("is_read") is False:
        data["read_at"] = None

    for field, value in data.items():
        setattr(notification, field, value)

    db.commit()
    db.refresh(notification)
    return _get_notification_detail_or_404(db, notification.id)

@router.post("/{notification_id}/read", response_model=NotificationDetailRead)
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)
    return _get_notification_detail_or_404(db, notification.id)