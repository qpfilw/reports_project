from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import ActiveMixin, BigIntIdMixin, TimestampMixin


class ProcessingScript(BigIntIdMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "processing_script"

    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_processing_script_code_version"),
        Index("ix_processing_script_target_report_type_id", "target_report_type_id"),
        Index("ix_processing_script_created_by", "created_by"),
        Index("ix_processing_script_is_active", "is_active"),
        Index("ix_processing_script_is_default", "is_default"),
    )

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    target_report_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("report_type.id", ondelete="SET NULL"),
        nullable=True,
    )

    script_code: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0", server_default="1.0")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    validation_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    target_report_type: Mapped["ReportType | None"] = relationship(
        "ReportType",
        back_populates="processing_scripts",
        foreign_keys=[target_report_type_id],
    )

    creator: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_processing_scripts",
        foreign_keys=[created_by],
    )

    ml_templates: Mapped[list["MlTemplate"]] = relationship(
        "MlTemplate",
        back_populates="processing_script",
        foreign_keys="MlTemplate.processing_script_id",
    )
