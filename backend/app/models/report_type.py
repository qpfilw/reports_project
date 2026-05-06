from __future__ import annotations

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import ActiveMixin, BigIntIdMixin, TimestampMixin


class ReportType(BigIntIdMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "report_type"

    __table_args__ = (
        UniqueConstraint("code", name="uq_report_type_code"),
        Index("ix_report_type_is_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
        server_default="1.0",
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="report_type",
    )

    uploads: Mapped[list["ReportUpload"]] = relationship(
        "ReportUpload",
        back_populates="report_type",
    )

    ml_templates: Mapped[list["MlTemplate"]] = relationship(
        "MlTemplate",
        back_populates="target_report_type",
        foreign_keys="MlTemplate.target_report_type_id",
    )

    processing_scripts: Mapped[list["ProcessingScript"]] = relationship(
        "ProcessingScript",
        back_populates="target_report_type",
        foreign_keys="ProcessingScript.target_report_type_id",
    )
