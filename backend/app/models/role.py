from __future__ import annotations

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship, mapped_column

from .base import Base
from .enums import RoleCodeEnum, enum_values
from .mixins import BigIntIdMixin, TimestampMixin


class Role(BigIntIdMixin, TimestampMixin, Base):
    __tablename__ = "role"

    __table_args__ = (
        UniqueConstraint("code", name="uq_role_code"),
        UniqueConstraint("name", name="uq_role_name"),
    )

    code: Mapped[RoleCodeEnum] = mapped_column(
        SAEnum(
            RoleCodeEnum,
            name="role_code_enum",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="role",
    )