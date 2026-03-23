from __future__ import annotations

from sqlalchemy import DateTime, Enum as SAEnum, String, Text
from sqlalchemy import ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ProjectAccessStatusEnum, ProjectMemberRoleEnum, enum_values
from .mixins import BigIntIdMixin


class ProjectMember(BigIntIdMixin, Base):
    __tablename__ = "project_member"

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member_project_user"),
        Index("ix_project_member_project_id", "project_id"),
        Index("ix_project_member_user_id", "user_id"),
        Index("ix_project_member_access_status", "access_status"),
        Index("ix_project_member_reviewed_by", "reviewed_by"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_role: Mapped[ProjectMemberRoleEnum] = mapped_column(
        SAEnum(
            ProjectMemberRoleEnum,
            name="project_member_role_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )

    access_status: Mapped[ProjectAccessStatusEnum] = mapped_column(
        SAEnum(
            ProjectAccessStatusEnum,
            name="project_access_status_enum",
            values_callable=enum_values,
        ),
        nullable=False,
        default=ProjectAccessStatusEnum.APPROVED,
        server_default=ProjectAccessStatusEnum.APPROVED.value,
    )

    added_by: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    added_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    requested_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    request_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="members",
        foreign_keys=[project_id],
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="project_memberships",
        foreign_keys=[user_id],
    )

    creator: Mapped["User | None"] = relationship(
        "User",
        back_populates="added_project_memberships",
        foreign_keys=[added_by],
    )

    reviewer: Mapped["User | None"] = relationship(
        "User",
        back_populates="reviewed_project_memberships",
        foreign_keys=[reviewed_by],
    )