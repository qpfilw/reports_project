from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey
from sqlalchemy import Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import BigIntIdMixin


class ReportUpload(BigIntIdMixin, Base):
    __tablename__ = "report_upload"

    __table_args__ = (
        UniqueConstraint("storage_path", name="uq_report_upload_storage_path"),
        UniqueConstraint("report_id", "upload_version", name="uq_report_upload_report_version"),
        CheckConstraint("upload_version >= 1", name="report_upload_version_positive"),
        CheckConstraint("file_size >= 0", name="report_upload_file_size_non_negative"),
        Index("ix_report_upload_report_id", "report_id"),
        Index("ix_report_upload_project_id", "project_id"),
        Index("ix_report_upload_report_type_id", "report_type_id"),
        Index("ix_report_upload_uploaded_by", "uploaded_by"),
        Index("ix_report_upload_checksum_sha256", "checksum_sha256"),
        Index("ix_report_upload_is_latest", "is_latest"),
    )

    report_id: Mapped[int] = mapped_column(
        ForeignKey("report.id", ondelete="CASCADE"),
        nullable=False,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_type_id: Mapped[int] = mapped_column(
        ForeignKey("report_type.id", ondelete="RESTRICT"),
        nullable=False,
    )
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    upload_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    uploaded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    report: Mapped["Report"] = relationship(
        "Report",
        back_populates="uploads",
        foreign_keys=[report_id],
    )

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="uploads",
        foreign_keys=[project_id],
    )

    report_type: Mapped["ReportType"] = relationship(
        "ReportType",
        back_populates="uploads",
        foreign_keys=[report_type_id],
    )

    uploader: Mapped["User"] = relationship(
        "User",
        back_populates="uploaded_files",
        foreign_keys=[uploaded_by],
    )

    processing_tasks: Mapped[list["ProcessingTask"]] = relationship(
        "ProcessingTask",
        back_populates="report_upload",
        cascade="all, delete-orphan",
    )