from __future__ import annotations

from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import BigIntIdMixin


class NormalizedDataset(BigIntIdMixin, Base):
    __tablename__ = "normalized_dataset"

    __table_args__ = (
        UniqueConstraint("processing_task_id", name="uq_normalized_dataset_processing_task_id"),
        CheckConstraint("rows_count >= 0", name="normalized_dataset_rows_count_non_negative"),
        Index("ix_normalized_dataset_report_id", "report_id"),
        Index("ix_normalized_dataset_created_at", "created_at"),
    )

    processing_task_id: Mapped[int] = mapped_column(
        ForeignKey("processing_task.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_id: Mapped[int] = mapped_column(
        ForeignKey("report.id", ondelete="CASCADE"),
        nullable=False,
    )

    rows_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    schema_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    summary_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    preview_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    data_location: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    processing_task: Mapped["ProcessingTask"] = relationship(
        "ProcessingTask",
        back_populates="normalized_dataset",
        foreign_keys=[processing_task_id],
    )

    report: Mapped["Report"] = relationship(
        "Report",
        back_populates="normalized_datasets",
        foreign_keys=[report_id],
    )

    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard",
        back_populates="normalized_dataset",
    )