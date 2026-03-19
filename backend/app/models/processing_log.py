from __future__ import annotations

from typing import Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ProcessingLogLevelEnum, enum_values
from .mixins import BigIntIdMixin


class ProcessingLog(BigIntIdMixin, Base):
    __tablename__ = "processing_log"

    __table_args__ = (
        Index("ix_processing_log_processing_task_id", "processing_task_id"),
        Index("ix_processing_log_level", "level"),
        Index("ix_processing_log_stage", "stage"),
        Index("ix_processing_log_created_at", "created_at"),
    )

    processing_task_id: Mapped[int] = mapped_column(
        ForeignKey("processing_task.id", ondelete="CASCADE"),
        nullable=False,
    )

    level: Mapped[ProcessingLogLevelEnum] = mapped_column(
        SAEnum(
            ProcessingLogLevelEnum,
            name="processing_log_level_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    context_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    processing_task: Mapped["ProcessingTask"] = relationship(
        "ProcessingTask",
        back_populates="logs",
        foreign_keys=[processing_task_id],
    )