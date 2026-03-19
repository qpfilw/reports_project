from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_active_user, get_db, require_operator_user
from app.models.enums import ProcessingLogLevelEnum
from app.models.ml_template import MlTemplate
from app.models.processing_log import ProcessingLog
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.models.report_upload import ReportUpload
from app.schemas.ml import (
    AnomalyItem,
    ColumnMappingConfirmRequest,
    ColumnMatchSuggestion,
    MLPipelineResult,
    TemplatePrediction,
    TemplatePredictionResult,
)
from app.schemas.template import MlTemplateRead, MlTemplateShortRead

router = APIRouter(dependencies=[Depends(get_current_active_user)])

def _select_templates_for_report_type(db: Session, report_type_id: int) -> list[MlTemplate]:
    stmt = (
        select(MlTemplate)
        .where(
            MlTemplate.target_report_type_id == report_type_id,
            MlTemplate.is_active.is_(True),
        )
        .order_by(MlTemplate.is_default.desc(), MlTemplate.id.asc())
    )
    return list(db.scalars(stmt).all())

def _build_prediction_result(templates: list[MlTemplate]) -> TemplatePredictionResult:
    candidates: list[TemplatePrediction] = []

    for index, template in enumerate(templates):
        if index == 0 and template.is_default:
            confidence = 0.95
        elif index == 0:
            confidence = 0.85
        else:
            confidence = max(0.5, 0.8 - (index * 0.1))

        candidates.append(
            TemplatePrediction(
                template_id=template.id,
                template_code=template.code,
                confidence=round(confidence, 2),
            )
        )

    best_match = candidates[0] if candidates else None
    return TemplatePredictionResult(best_match=best_match, candidates=candidates)

def _build_pipeline_result(task: ProcessingTask) -> MLPipelineResult:
    selected_template = (
        MlTemplateShortRead.model_validate(task.ml_template)
        if task.ml_template is not None
        else None
    )

    params = dict(task.params_json or {})

    matches_data = params.get("confirmed_mappings") or params.get("column_matches") or []
    column_matches = [ColumnMatchSuggestion.model_validate(item) for item in matches_data]

    anomalies = [
        AnomalyItem(
            row_number=error.row_number,
            field_path=error.field_path,
            anomaly_type=error.error_type,
            severity="critical" if error.is_critical else "warning",
            message=error.details or error.error_code,
            source_value=error.source_value,
            confidence=None,
        )
        for error in task.errors
    ]

    prediction = None
    if task.ml_template is not None:
        prediction = TemplatePredictionResult(
            best_match=TemplatePrediction(
                template_id=task.ml_template.id,
                template_code=task.ml_template.code,
                confidence=float(task.quality_score) if task.quality_score is not None else 0.9,
            ),
            candidates=[],
        )

    diagnostics = {
        "status": task.status,
        "warning_count": task.warning_count,
        "error_count": task.error_count,
        "retry_count": task.retry_count,
        "params_keys": list(params.keys()),
    }

    return MLPipelineResult(
        selected_template=selected_template,
        template_prediction=prediction,
        column_matches=column_matches,
        anomalies=anomalies,
        quality_score=float(task.quality_score) if task.quality_score is not None else None,
        diagnostics=diagnostics,
    )

@router.get("/templates", response_model=list[MlTemplateRead])
def list_ml_templates(
    report_type_id: int | None = Query(default=None),
    only_active: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> list[MlTemplate]:
    stmt = select(MlTemplate)

    if report_type_id is not None:
        stmt = stmt.where(MlTemplate.target_report_type_id == report_type_id)
    if only_active:
        stmt = stmt.where(MlTemplate.is_active.is_(True))

    stmt = stmt.order_by(MlTemplate.is_default.desc(), MlTemplate.id.asc())
    return list(db.scalars(stmt).all())

@router.get("/reports/{report_id}/template-prediction", response_model=TemplatePredictionResult)
def predict_template_for_report(report_id: int, db: Session = Depends(get_db)) -> TemplatePredictionResult:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    templates = _select_templates_for_report_type(db, report.report_type_id)
    return _build_prediction_result(templates)

@router.get("/uploads/{upload_id}/template-prediction", response_model=TemplatePredictionResult)
def predict_template_for_upload(upload_id: int, db: Session = Depends(get_db)) -> TemplatePredictionResult:
    upload = db.get(ReportUpload, upload_id)
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")

    templates = _select_templates_for_report_type(db, upload.report_type_id)
    return _build_prediction_result(templates)

@router.get("/tasks/{task_id}/pipeline-result", response_model=MLPipelineResult)
def get_ml_pipeline_result(task_id: int, db: Session = Depends(get_db)) -> MLPipelineResult:
    stmt = (
        select(ProcessingTask)
        .options(
            selectinload(ProcessingTask.ml_template),
            selectinload(ProcessingTask.errors),
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    return _build_pipeline_result(task)

@router.post("/tasks/{task_id}/confirm-mapping", response_model=MLPipelineResult, dependencies=[Depends(require_operator_user)])
def confirm_column_mapping(
    task_id: int,
    payload: ColumnMappingConfirmRequest,
    db: Session = Depends(get_db),
) -> MLPipelineResult:
    stmt = (
        select(ProcessingTask)
        .options(
            selectinload(ProcessingTask.ml_template),
            selectinload(ProcessingTask.errors),
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    params = dict(task.params_json or {})
    params["confirmed_mappings"] = [item.model_dump() for item in payload.mappings]
    task.params_json = params

    log = ProcessingLog(
        processing_task_id=task.id,
        level=ProcessingLogLevelEnum.INFO,
        stage="column_mapping",
        message="Column mappings were confirmed manually.",
        context_json={"mapping_count": len(payload.mappings)},
    )
    db.add(log)

    db.commit()
    db.refresh(task)

    stmt = (
        select(ProcessingTask)
        .options(
            selectinload(ProcessingTask.ml_template),
            selectinload(ProcessingTask.errors),
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    return _build_pipeline_result(task)