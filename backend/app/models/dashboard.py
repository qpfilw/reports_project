from __future__ import annotations

from typing import Any
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import DashboardSourceTypeEnum, DashboardTypeEnum, enum_values
from .mixins import BigIntIdMixin, TimestampMixin


class Dashboard(BigIntIdMixin, TimestampMixin, Base):
    __tablename__ = "dashboard"

    __table_args__ = (
        UniqueConstraint("owner_id", "project_id", "name", name="uq_dashboard_owner_project_name"),
        Index("ix_dashboard_project_id", "project_id"),
        Index("ix_dashboard_report_id", "report_id"),
        Index("ix_dashboard_normalized_dataset_id", "normalized_dataset_id"),
        Index("ix_dashboard_owner_id", "owner_id"),
        Index("ix_dashboard_dashboard_type", "dashboard_type"),
        Index("ix_dashboard_source_type", "source_type"),
    )

    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("report.id", ondelete="SET NULL"), nullable=True)
    normalized_dataset_id: Mapped[int | None] = mapped_column(ForeignKey("normalized_dataset.id", ondelete="SET NULL"), nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    dashboard_type: Mapped[DashboardTypeEnum] = mapped_column(
        SAEnum(
            DashboardTypeEnum,
            name="dashboard_type_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    source_type: Mapped[DashboardSourceTypeEnum] = mapped_column(
        SAEnum(
            DashboardSourceTypeEnum,
            name="dashboard_source_type_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )

    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    layout_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    last_generated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="dashboards", foreign_keys=[project_id])
    report: Mapped["Report | None"] = relationship("Report", back_populates="dashboards", foreign_keys=[report_id])
    normalized_dataset: Mapped["NormalizedDataset | None"] = relationship("NormalizedDataset", back_populates="dashboards", foreign_keys=[normalized_dataset_id])
    owner: Mapped["User"] = relationship("User", back_populates="dashboards", foreign_keys=[owner_id])
    export_artifacts: Mapped[list["ExportArtifact"]] = relationship("ExportArtifact", back_populates="dashboard")