from __future__ import annotations

from sqlalchemy import CheckConstraint, Date, DateTime, Enum as SAEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ReportStatusEnum, enum_values
from .mixins import ArchiveMixin, BigIntIdMixin, TimestampMixin


class Report(BigIntIdMixin, TimestampMixin, ArchiveMixin, Base):
    __tablename__ = "report"

    __table_args__ = (
        CheckConstraint(
            "report_period_end >= report_period_start",
            name="report_period_range_valid",
        ),
        Index("ix_report_project_id", "project_id"),
        Index("ix_report_report_type_id", "report_type_id"),
        Index("ix_report_creator_id", "creator_id"),
        Index("ix_report_status", "status"),
        Index("ix_report_ml_template_id", "ml_template_id"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_type_id: Mapped[int] = mapped_column(
        ForeignKey("report_type.id", ondelete="RESTRICT"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    report_period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    report_period_end: Mapped[Date] = mapped_column(Date, nullable=False)

    status: Mapped[ReportStatusEnum] = mapped_column(
        SAEnum(
            ReportStatusEnum,
            name="report_status_enum",
            values_callable=enum_values,
        ),
        nullable=False,
        default=ReportStatusEnum.DRAFT,
        server_default=ReportStatusEnum.DRAFT.value,
    )

    creator_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approver_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    ml_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("ml_template.id", ondelete="SET NULL"),
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    submitted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejected_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="reports",
        foreign_keys=[project_id],
    )

    report_type: Mapped["ReportType"] = relationship(
        "ReportType",
        back_populates="reports",
        foreign_keys=[report_type_id],
    )

    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_reports",
        foreign_keys=[creator_id],
    )

    current_assignee: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_reports",
        foreign_keys=[current_assignee_id],
    )

    approver: Mapped["User | None"] = relationship(
        "User",
        back_populates="approved_reports",
        foreign_keys=[approver_id],
    )

    ml_template: Mapped["MlTemplate | None"] = relationship(
        "MlTemplate",
        back_populates="reports",
        foreign_keys=[ml_template_id],
    )

    uploads: Mapped[list["ReportUpload"]] = relationship(
        "ReportUpload",
        back_populates="report",
        cascade="all, delete-orphan",
    )

    processing_tasks: Mapped[list["ProcessingTask"]] = relationship(
        "ProcessingTask",
        back_populates="report",
    )

    normalized_datasets: Mapped[list["NormalizedDataset"]] = relationship(
        "NormalizedDataset",
        back_populates="report",
    )

    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard",
        back_populates="report",
    )

    export_artifacts: Mapped[list["ExportArtifact"]] = relationship(
        "ExportArtifact",
        back_populates="report",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="report",
    )