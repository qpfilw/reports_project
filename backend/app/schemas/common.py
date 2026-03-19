from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        extra="ignore",
    )

class IdSchema(BaseSchema):
    id: int

class CreatedAtSchema(BaseSchema):
    created_at: datetime

class TimestampSchema(CreatedAtSchema):
    updated_at: datetime

class MessageSchema(BaseSchema):
    message: str