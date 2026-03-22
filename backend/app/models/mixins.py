from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, func
from sqlalchemy.orm import Mapped, mapped_column

class BigIntIdMixin:
    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=False),
        primary_key=True,
    )

class CreatedAtMixin:
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

class ActiveMixin:
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

class ArchiveMixin:
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )