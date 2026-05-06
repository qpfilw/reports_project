from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import TemplateTypeEnum, enum_values
from .mixins import ActiveMixin, BigIntIdMixin, TimestampMixin


class MlTemplate(BigIntIdMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "ml_template"

    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_ml_template_code_version"),
        Index("ix_ml_template_target_report_type_id", "target_report_type_id"),
        Index("ix_ml_template_processing_script_id", "processing_script_id"),
        Index("ix_ml_template_created_by", "created_by"),
        Index("ix_ml_template_is_active", "is_active"),
        Index("ix_ml_template_is_default", "is_default"),
    )

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    template_type: Mapped[TemplateTypeEnum] = mapped_column(
        SAEnum(
            TemplateTypeEnum,
            name="template_type_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )

    target_report_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("report_type.id", ondelete="SET NULL"),
        nullable=True,
    )

    department: Mapped[str | None] = mapped_column(String(150), nullable=True)

    processing_script_id: Mapped[int | None] = mapped_column(
        ForeignKey("processing_script.id", ondelete="SET NULL"),
        nullable=True,
    )

    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    model_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0",
        server_default="1.0",
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    target_report_type: Mapped["ReportType | None"] = relationship(
        "ReportType",
        back_populates="ml_templates",
        foreign_keys=[target_report_type_id],
    )

    creator: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_ml_templates",
        foreign_keys=[created_by],
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="ml_template",
        foreign_keys="Report.ml_template_id",
    )

    processing_script: Mapped["ProcessingScript | None"] = relationship(
        "ProcessingScript",
        back_populates="ml_templates",
        foreign_keys=[processing_script_id],
    )

    processing_tasks: Mapped[list["ProcessingTask"]] = relationship(
        "ProcessingTask",
        back_populates="ml_template",
        foreign_keys="ProcessingTask.ml_template_id",
    )