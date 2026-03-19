from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import BigIntIdMixin


class TaskError(BigIntIdMixin, Base):
    __tablename__ = "task_error"

    __table_args__ = (
        Index("ix_task_error_processing_task_id", "processing_task_id"),
        Index("ix_task_error_error_code", "error_code"),
        Index("ix_task_error_error_type", "error_type"),
        Index("ix_task_error_row_number", "row_number"),
        Index("ix_task_error_is_critical", "is_critical"),
    )

    processing_task_id: Mapped[int] = mapped_column(
        ForeignKey("processing_task.id", ondelete="CASCADE"),
        nullable=False,
    )

    error_code: Mapped[str] = mapped_column(String(100), nullable=False)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    field_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_critical: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    processing_task: Mapped["ProcessingTask"] = relationship(
        "ProcessingTask",
        back_populates="errors",
        foreign_keys=[processing_task_id],
    )