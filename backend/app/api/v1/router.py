from __future__ import annotations
from fastapi import APIRouter

from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.ml import router as ml_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.processing import router as processing_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.report_types import router as report_types_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.results import router as results_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.templates import router as templates_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.users import router as users_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(roles_router, prefix="/roles", tags=["roles"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(projects_router, prefix="/projects", tags=["projects"])
router.include_router(report_types_router, prefix="/report-types", tags=["report-types"])
router.include_router(templates_router, prefix="/templates", tags=["templates"])
router.include_router(reports_router, prefix="/reports", tags=["reports"])
router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
router.include_router(processing_router, prefix="/processing", tags=["processing"])
router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(results_router, prefix="/results", tags=["results"])
router.include_router(exports_router, prefix="/exports", tags=["exports"])
router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
router.include_router(audit_router, prefix="/audit", tags=["audit"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(ml_router, prefix="/ml", tags=["ml"])