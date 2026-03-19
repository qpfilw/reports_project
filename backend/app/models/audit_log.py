from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy import Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import AuditActionEnum, AuditEntityTypeEnum, enum_values
from .mixins import BigIntIdMixin


class AuditLog(BigIntIdMixin, Base):
    __tablename__ = "audit_log"

    __table_args__ = (
        Index("ix_audit_log_user_id", "user_id"),
        Index("ix_audit_log_project_id", "project_id"),
        Index("ix_audit_log_action", "action"),
        Index("ix_audit_log_entity_type", "entity_type"),
        Index("ix_audit_log_entity_id", "entity_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )

    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("project.id", ondelete="SET NULL"), nullable=True)

    action: Mapped[AuditActionEnum] = mapped_column(
        SAEnum(
            AuditActionEnum,
            name="audit_action_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    entity_type: Mapped[AuditEntityTypeEnum] = mapped_column(
        SAEnum(
            AuditEntityTypeEnum,
            name="audit_entity_type_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    before_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs", foreign_keys=[user_id])
    project: Mapped["Project | None"] = relationship("Project", back_populates="audit_logs", foreign_keys=[project_id])