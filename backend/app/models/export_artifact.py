from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy import Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ExportFormatEnum, enum_values
from .mixins import BigIntIdMixin


class ExportArtifact(BigIntIdMixin, Base):
    __tablename__ = "export_artifact"

    __table_args__ = (
        UniqueConstraint("storage_path", name="uq_export_artifact_storage_path"),
        CheckConstraint("file_size >= 0", name="export_artifact_file_size_non_negative"),
        CheckConstraint(
            "processing_task_id IS NOT NULL OR report_id IS NOT NULL OR dashboard_id IS NOT NULL",
            name="export_artifact_has_source",
        ),
        Index("ix_export_artifact_processing_task_id", "processing_task_id"),
        Index("ix_export_artifact_report_id", "report_id"),
        Index("ix_export_artifact_dashboard_id", "dashboard_id"),
        Index("ix_export_artifact_created_by", "created_by"),
        Index("ix_export_artifact_format", "format"),
    )

    processing_task_id: Mapped[int | None] = mapped_column(ForeignKey("processing_task.id", ondelete="SET NULL"), nullable=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("report.id", ondelete="SET NULL"), nullable=True)
    dashboard_id: Mapped[int | None] = mapped_column(ForeignKey("dashboard.id", ondelete="SET NULL"), nullable=True)

    format: Mapped[ExportFormatEnum] = mapped_column(
        SAEnum(
            ExportFormatEnum,
            name="export_format_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    processing_task: Mapped["ProcessingTask | None"] = relationship("ProcessingTask", back_populates="export_artifacts", foreign_keys=[processing_task_id])
    report: Mapped["Report | None"] = relationship("Report", back_populates="export_artifacts", foreign_keys=[report_id])
    dashboard: Mapped["Dashboard | None"] = relationship("Dashboard", back_populates="export_artifacts", foreign_keys=[dashboard_id])
    creator: Mapped["User | None"] = relationship("User", back_populates="created_exports", foreign_keys=[created_by])