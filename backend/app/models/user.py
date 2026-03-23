from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import BigIntIdMixin, TimestampMixin


class User(BigIntIdMixin, TimestampMixin, Base):
    __tablename__ = "user"

    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        Index("ix_user_role_id", "role_id"),
        Index("ix_user_is_active", "is_active"),
        Index("ix_user_is_blocked", "is_blocked"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str | None] = mapped_column(String(150), nullable=True)
    department: Mapped[str | None] = mapped_column(String(150), nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    last_login_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("role.id", ondelete="RESTRICT"),
        nullable=False,
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
    )

    owned_projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        foreign_keys="Project.owner_id",
    )

    project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        foreign_keys="ProjectMember.user_id",
    )

    added_project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="creator",
        foreign_keys="ProjectMember.added_by",
    )

    reviewed_project_memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="reviewer",
        foreign_keys="ProjectMember.reviewed_by",
    )

    created_reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="creator",
        foreign_keys="Report.creator_id",
    )

    assigned_reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="current_assignee",
        foreign_keys="Report.current_assignee_id",
    )

    approved_reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="approver",
        foreign_keys="Report.approver_id",
    )

    uploaded_files: Mapped[list["ReportUpload"]] = relationship(
        "ReportUpload",
        back_populates="uploader",
        foreign_keys="ReportUpload.uploaded_by",
    )

    created_processing_tasks: Mapped[list["ProcessingTask"]] = relationship(
        "ProcessingTask",
        back_populates="creator",
        foreign_keys="ProcessingTask.created_by",
    )

    created_exports: Mapped[list["ExportArtifact"]] = relationship(
        "ExportArtifact",
        back_populates="creator",
        foreign_keys="ExportArtifact.created_by",
    )

    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard",
        back_populates="owner",
        foreign_keys="Dashboard.owner_id",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        foreign_keys="Notification.user_id",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="AuditLog.user_id",
    )

    created_ml_templates: Mapped[list["MlTemplate"]] = relationship(
        "MlTemplate",
        back_populates="creator",
        foreign_keys="MlTemplate.created_by",
    )