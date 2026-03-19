from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import ArchiveMixin, BigIntIdMixin, TimestampMixin


class Project(BigIntIdMixin, TimestampMixin, ArchiveMixin, Base):
    __tablename__ = "project"

    __table_args__ = (
        UniqueConstraint("code", name="uq_project_code"),
        UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
        Index("ix_project_owner_id", "owner_id"),
        Index("ix_project_is_archived", "is_archived"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_projects",
        foreign_keys=[owner_id],
    )

    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="project",
    )

    uploads: Mapped[list["ReportUpload"]] = relationship(
        "ReportUpload",
        back_populates="project",
    )

    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard",
        back_populates="project",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="project",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="project",
    )