from __future__ import annotations

from typing import Any
from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy import Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .enums import ProcessingStatusEnum, enum_values
from .mixins import BigIntIdMixin, CreatedAtMixin


class ProcessingTask(BigIntIdMixin, CreatedAtMixin, Base):
    __tablename__ = "processing_task"

    __table_args__ = (
        UniqueConstraint("celery_task_id", name="uq_processing_task_celery_task_id"),
        CheckConstraint("progress >= 0 AND progress <= 100", name="processing_task_progress_range"),
        CheckConstraint("priority >= 1 AND priority <= 10", name="processing_task_priority_range"),
        CheckConstraint(
            "(quality_score IS NULL) OR (quality_score >= 0 AND quality_score <= 1)",
            name="processing_task_quality_score_range",
        ),
        CheckConstraint("warning_count >= 0", name="processing_task_warning_count_non_negative"),
        CheckConstraint("error_count >= 0", name="processing_task_error_count_non_negative"),
        CheckConstraint("retry_count >= 0", name="processing_task_retry_count_non_negative"),
        Index("ix_processing_task_report_id", "report_id"),
        Index("ix_processing_task_report_upload_id", "report_upload_id"),
        Index("ix_processing_task_ml_template_id", "ml_template_id"),
        Index("ix_processing_task_created_by", "created_by"),
        Index("ix_processing_task_status", "status"),
        Index("ix_processing_task_queued_at", "queued_at"),
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey("report.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_upload_id: Mapped[int] = mapped_column(
        ForeignKey("report_upload.id", ondelete="CASCADE"),
        nullable=False,
    )
    ml_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_template.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[ProcessingStatusEnum] = mapped_column(
        SAEnum(
            ProcessingStatusEnum,
            name="processing_status_enum",
            values_callable=enum_values,
        ),
        nullable=False,
        default=ProcessingStatusEnum.QUEUED,
        server_default=ProcessingStatusEnum.QUEUED.value,
    )

    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default="5")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    params_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    queued_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    report: Mapped["Report"] = relationship("Report", back_populates="processing_tasks", foreign_keys=[report_id])
    report_upload: Mapped["ReportUpload"] = relationship("ReportUpload", back_populates="processing_tasks", foreign_keys=[report_upload_id])
    ml_template: Mapped["MlTemplate | None"] = relationship("MlTemplate", back_populates="processing_tasks", foreign_keys=[ml_template_id])
    creator: Mapped["User | None"] = relationship("User", back_populates="created_processing_tasks", foreign_keys=[created_by])

    logs: Mapped[list["ProcessingLog"]] = relationship("ProcessingLog", back_populates="processing_task", cascade="all, delete-orphan")
    errors: Mapped[list["TaskError"]] = relationship("TaskError", back_populates="processing_task", cascade="all, delete-orphan")
    normalized_dataset: Mapped["NormalizedDataset | None"] = relationship("NormalizedDataset", back_populates="processing_task", uselist=False, cascade="all, delete-orphan")
    export_artifacts: Mapped[list["ExportArtifact"]] = relationship("ExportArtifact", back_populates="processing_task")
    notifications: Mapped[list["Notification"]] = relationship("Notification", back_populates="processing_task")