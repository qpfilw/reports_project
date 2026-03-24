from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from fastapi import HTTPException, status

@dataclass
class AppError(Exception):
    detail: str
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "APP_ERROR"
    extra: dict[str, Any] | None = None

    def to_http_exception(self) -> HTTPException:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.detail,
        }
        if self.extra:
            payload["extra"] = self.extra
        return HTTPException(status_code=self.status_code, detail=payload)


@dataclass
class AccessDeniedError(AppError):
    detail: str = "Access denied."
    status_code: int = status.HTTP_403_FORBIDDEN
    code: str = "ACCESS_DENIED"


@dataclass
class AuthenticationRequiredError(AppError):
    detail: str = "Authentication required."
    status_code: int = status.HTTP_401_UNAUTHORIZED
    code: str = "AUTHENTICATION_REQUIRED"


@dataclass
class ObjectNotFoundError(AppError):
    detail: str = "Object not found."
    status_code: int = status.HTTP_404_NOT_FOUND
    code: str = "OBJECT_NOT_FOUND"


@dataclass
class ProjectScopeMismatchError(AppError):
    detail: str = "Objects belong to different projects."
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "PROJECT_SCOPE_MISMATCH"


@dataclass
class InvalidWorkflowTransitionError(AppError):
    detail: str = "Invalid workflow transition."
    status_code: int = status.HTTP_409_CONFLICT
    code: str = "INVALID_WORKFLOW_TRANSITION"


@dataclass
class ValidationPipelineError(AppError):
    detail: str = "Validation pipeline failed."
    status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT
    code: str = "VALIDATION_PIPELINE_ERROR"


@dataclass
class TemplateMismatchError(AppError):
    detail: str = "ML template does not match report type."
    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "TEMPLATE_MISMATCH"


@dataclass
class ProcessingLaunchError(AppError):
    detail: str = "Processing task cannot be launched."
    status_code: int = status.HTTP_409_CONFLICT
    code: str = "PROCESSING_LAUNCH_ERROR"


@dataclass
class ExportGenerationError(AppError):
    detail: str = "Export generation failed."
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "EXPORT_GENERATION_ERROR"


def raise_http(error: AppError) -> None:
    raise error.to_http_exception()