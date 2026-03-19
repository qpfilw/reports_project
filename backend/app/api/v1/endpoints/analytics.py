from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db, require_manager_user
from app.models.dashboard import Dashboard
from app.models.export_artifact import ExportArtifact
from app.models.normalized_dataset import NormalizedDataset
from app.models.processing_task import ProcessingTask
from app.models.project import Project
from app.models.report import Report
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    DashboardCreate,
    DashboardDetailRead,
    DashboardMetricItem,
    DashboardRead,
    DashboardUpdate,
)

router = APIRouter(dependencies=[Depends(get_current_active_user)])

def _get_dashboard_detail_or_404(db: Session, dashboard_id: int) -> Dashboard:
    stmt = (
        select(Dashboard)
        .options(
            selectinload(Dashboard.owner),
            selectinload(Dashboard.report),
            selectinload(Dashboard.normalized_dataset),
        )
        .where(Dashboard.id == dashboard_id)
    )
    dashboard = db.scalar(stmt)
    if dashboard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")
    return dashboard

@router.get("/dashboards", response_model=list[DashboardRead])
def list_dashboards(db: Session = Depends(get_db)) -> list[Dashboard]:
    stmt = select(Dashboard).order_by(Dashboard.id.desc())
    return list(db.scalars(stmt).all())

@router.get("/dashboards/{dashboard_id}", response_model=DashboardDetailRead)
def get_dashboard(dashboard_id: int, db: Session = Depends(get_db)) -> Dashboard:
    return _get_dashboard_detail_or_404(db, dashboard_id)

@router.post("/dashboards", response_model=DashboardDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager_user)])
def create_dashboard(payload: DashboardCreate, db: Session = Depends(get_db)) -> Dashboard:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    owner = db.get(User, payload.owner_id)
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found.")

    if payload.report_id is not None:
        report = db.get(Report, payload.report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if payload.normalized_dataset_id is not None:
        dataset = db.get(NormalizedDataset, payload.normalized_dataset_id)
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Normalized dataset not found.")

    existing = db.scalar(
        select(Dashboard).where(
            Dashboard.owner_id == payload.owner_id,
            Dashboard.project_id == payload.project_id,
            Dashboard.name == payload.name,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dashboard with this name already exists for this owner in the project.",
        )

    dashboard = Dashboard(**payload.model_dump())
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return _get_dashboard_detail_or_404(db, dashboard.id)

@router.patch("/dashboards/{dashboard_id}", response_model=DashboardDetailRead, dependencies=[Depends(require_manager_user)])
def update_dashboard(
    dashboard_id: int,
    payload: DashboardUpdate,
    db: Session = Depends(get_db),
) -> Dashboard:
    dashboard = db.get(Dashboard, dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found.")

    data = payload.model_dump(exclude_unset=True)

    if "report_id" in data and data["report_id"] is not None:
        report = db.get(Report, data["report_id"])
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if "normalized_dataset_id" in data and data["normalized_dataset_id"] is not None:
        dataset = db.get(NormalizedDataset, data["normalized_dataset_id"])
        if dataset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Normalized dataset not found.")

    if "name" in data:
        existing = db.scalar(
            select(Dashboard).where(
                Dashboard.owner_id == dashboard.owner_id,
                Dashboard.project_id == dashboard.project_id,
                Dashboard.name == data["name"],
                Dashboard.id != dashboard_id,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dashboard with this name already exists for this owner in the project.",
            )

    for field, value in data.items():
        setattr(dashboard, field, value)

    db.commit()
    db.refresh(dashboard)
    return _get_dashboard_detail_or_404(db, dashboard.id)

@router.get("/overview", response_model=AnalyticsOverview, dependencies=[Depends(require_manager_user)])
def analytics_overview(db: Session = Depends(get_db)) -> AnalyticsOverview:
    total_reports = db.scalar(select(func.count()).select_from(Report)) or 0
    total_tasks = db.scalar(select(func.count()).select_from(ProcessingTask)) or 0
    total_exports = db.scalar(select(func.count()).select_from(ExportArtifact)) or 0
    total_dashboards = db.scalar(select(func.count()).select_from(Dashboard)) or 0

    successful_tasks = db.scalar(
        select(func.count()).select_from(ProcessingTask).where(ProcessingTask.status == "success")
    ) or 0
    failed_tasks = db.scalar(
        select(func.count()).select_from(ProcessingTask).where(ProcessingTask.status == "failed")
    ) or 0

    avg_quality = db.scalar(select(func.avg(ProcessingTask.quality_score)).where(ProcessingTask.quality_score.is_not(None)))

    metrics = [
        DashboardMetricItem(key="reports", label="Reports", value=total_reports),
        DashboardMetricItem(key="tasks", label="Tasks", value=total_tasks),
        DashboardMetricItem(key="successful_tasks", label="Successful tasks", value=successful_tasks),
        DashboardMetricItem(key="failed_tasks", label="Failed tasks", value=failed_tasks),
        DashboardMetricItem(key="exports", label="Exports", value=total_exports),
        DashboardMetricItem(key="dashboards", label="Dashboards", value=total_dashboards),
    ]

    return AnalyticsOverview(
        total_reports=total_reports,
        total_uploads=0,
        total_tasks=total_tasks,
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks,
        total_exports=total_exports,
        average_quality_score=float(avg_quality) if avg_quality is not None else None,
        metrics=metrics,
    )