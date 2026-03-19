from __future__ import annotations
from .common import BaseSchema

class AdminOverview(BaseSchema):
    total_users: int = 0
    active_users: int = 0
    blocked_users: int = 0
    total_projects: int = 0
    archived_projects: int = 0
    total_reports: int = 0
    total_tasks: int = 0
    total_failed_tasks: int = 0
    total_notifications: int = 0
    unread_notifications: int = 0
    total_audit_logs: int = 0