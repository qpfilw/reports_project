from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy import Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import NotificationTypeEnum, enum_values
from .mixins import BigIntIdMixin


class Notification(BigIntIdMixin, Base):
    __tablename__ = "notification"

    __table_args__ = (
        Index("ix_notification_user_id", "user_id"),
        Index("ix_notification_project_id", "project_id"),
        Index("ix_notification_report_id", "report_id"),
        Index("ix_notification_processing_task_id", "processing_task_id"),
        Index("ix_notification_type", "type"),
        Index("ix_notification_is_read", "is_read"),
        Index("ix_notification_created_at", "created_at"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), nullable=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("report.id", ondelete="SET NULL"), nullable=True)
    processing_task_id: Mapped[int | None] = mapped_column(ForeignKey("processing_task.id", ondelete="SET NULL"), nullable=True)

    type: Mapped[NotificationTypeEnum] = mapped_column(
        SAEnum(
            NotificationTypeEnum,
            name="notification_type_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    read_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="notifications", foreign_keys=[user_id])
    project: Mapped["Project | None"] = relationship("Project", back_populates="notifications", foreign_keys=[project_id])
    report: Mapped["Report | None"] = relationship("Report", back_populates="notifications", foreign_keys=[report_id])
    processing_task: Mapped["ProcessingTask | None"] = relationship("ProcessingTask", back_populates="notifications", foreign_keys=[processing_task_id])