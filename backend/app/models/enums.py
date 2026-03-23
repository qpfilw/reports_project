from __future__ import annotations

from enum import Enum


class RoleCodeEnum(str, Enum):
    PENDING = "pending"
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class ProjectMemberRoleEnum(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"


class ProjectAccessStatusEnum(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReportStatusEnum(str, Enum):
    DRAFT = "draft"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ON_REVIEW = "on_review"
    ON_APPROVAL = "on_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    REWORK = "rework"
    ARCHIVED = "archived"


class ProcessingStatusEnum(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class ProcessingLogLevelEnum(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class TemplateTypeEnum(str, Enum):
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    NORMALIZATION = "normalization"
    HYBRID = "hybrid"


class ExportFormatEnum(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class DashboardTypeEnum(str, Enum):
    PERSONAL = "personal"
    DEPARTMENT = "department"
    EXECUTIVE = "executive"
    SYSTEM = "system"


class DashboardSourceTypeEnum(str, Enum):
    NORMALIZED_DATASET = "normalized_dataset"
    REPORT = "report"
    PROJECT_AGGREGATE = "project_aggregate"


class NotificationTypeEnum(str, Enum):
    REPORT_STATUS_CHANGED = "report_status_changed"
    REPORT_SUBMITTED = "report_submitted"
    REPORT_APPROVED = "report_approved"
    REPORT_REJECTED = "report_rejected"
    TASK_FAILED = "task_failed"
    TASK_COMPLETED = "task_completed"
    SYSTEM_ALERT = "system_alert"


class AuditActionEnum(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    PROCESS_START = "process_start"
    PROCESS_RETRY = "process_retry"
    PROCESS_FINISH = "process_finish"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"


class AuditEntityTypeEnum(str, Enum):
    USER = "user"
    PROJECT = "project"
    REPORT = "report"
    REPORT_UPLOAD = "report_upload"
    TEMPLATE = "template"
    TASK = "task"
    DASHBOARD = "dashboard"


def enum_values(enum_cls: type[Enum]) -> list[str]:
    return [item.value for item in enum_cls]