from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditActionEnum, AuditEntityTypeEnum


def _jsonify(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonify(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonify(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def get_request_meta(request: Request | None) -> tuple[str | None, str | None]:
    if request is None:
        return None, None
    ip_address = request.client.host if request.client is not None else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


def write_audit_log(
    db: Session,
    *,
    action: AuditActionEnum,
    entity_type: AuditEntityTypeEnum,
    entity_id: int | None = None,
    user_id: int | None = None,
    project_id: int | None = None,
    before_json: dict[str, Any] | None = None,
    after_json: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    ip_address, user_agent = get_request_meta(request)
    audit_log = AuditLog(
        user_id=user_id,
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=_jsonify(before_json) if before_json is not None else None,
        after_json=_jsonify(after_json) if after_json is not None else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    db.flush()
    return audit_log
