from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_approved_user, get_db, require_operator_user
from app.core.access import ensure_project_read_access, ensure_project_write_access
from app.models.enums import ProcessingLogLevelEnum
from app.models.ml_template import MlTemplate
from app.models.processing_log import ProcessingLog
from app.models.processing_task import ProcessingTask
from app.models.report import Report
from app.models.report_upload import ReportUpload
from app.models.user import User
from app.schemas.ml import (
    AnomalyItem,
    ColumnMappingConfirmRequest,
    ColumnMatchSuggestion,
    MLPipelineResult,
    TemplatePrediction,
    TemplatePredictionResult,
)
from app.schemas.template import MlTemplateRead, MlTemplateShortRead
from app.services.ml_service import MLService

router = APIRouter(dependencies=[Depends(require_approved_user)])


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



def _to_prediction_result(prediction_payload: dict[str, object]) -> TemplatePredictionResult:
    best = prediction_payload.get("best")
    best_match = None
    if isinstance(best, dict):
        template = best["template"]
        best_match = TemplatePrediction(
            template_id=template.id,
            template_code=template.code,
            confidence=float(best["confidence"]),
        )

    candidates: list[TemplatePrediction] = []
    for item in prediction_payload.get("candidates", []):
        template = item["template"]
        candidates.append(
            TemplatePrediction(
                template_id=template.id,
                template_code=template.code,
                confidence=float(item["confidence"]),
            )
        )
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
    prediction_payload = params.get("prediction_candidates")
    best_match_payload = (params.get("ml_prediction") or {}).get("best_match")
    if prediction_payload or best_match_payload:
        candidates = [
            TemplatePrediction(
                template_id=item.get("template_id"),
                template_code=item.get("template_code"),
                confidence=float(item.get("confidence", 0.0)),
            )
            for item in prediction_payload or []
        ]
        best_match = None
        if best_match_payload:
            best_match = TemplatePrediction(
                template_id=best_match_payload.get("template_id"),
                template_code=best_match_payload.get("template_code"),
                confidence=float(best_match_payload.get("confidence", 0.0)),
            )
        prediction = TemplatePredictionResult(best_match=best_match, candidates=candidates)
    elif task.ml_template is not None:
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
        "headers": params.get("headers") or [],
        "unmatched_headers": params.get("unmatched_headers") or [],
        "selection_mode": (params.get("ml_prediction") or {}).get("selection_mode"),
    }

    return MLPipelineResult(
        selected_template=selected_template,
        template_prediction=prediction,
        column_matches=column_matches,
        anomalies=anomalies,
        quality_score=float(task.quality_score) if task.quality_score is not None else None,
        mapping_confirmation_required=bool(params.get("mapping_confirmation_required", False)),
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
def predict_template_for_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> TemplatePredictionResult:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    ensure_project_read_access(db, project_id=report.project_id, current_user=current_user)

    latest_upload = db.scalar(
        select(ReportUpload)
        .where(ReportUpload.report_id == report.id, ReportUpload.is_latest.is_(True))
        .order_by(ReportUpload.upload_version.desc())
    )
    if latest_upload is not None:
        ml_service = MLService(db)
        payload = ml_service.analyze_upload(upload=latest_upload, forced_template_id=report.ml_template_id)
        return _to_prediction_result(payload["prediction"])

    templates = _select_templates_for_report_type(db, report.report_type_id)
    payload = {"best": None, "candidates": []}
    if templates:
        payload = {
            "best": {"template": templates[0], "confidence": 0.65},
            "candidates": [{"template": template, "confidence": 0.65 if idx == 0 else max(0.45, 0.6 - idx * 0.05)} for idx, template in enumerate(templates)],
        }
    return _to_prediction_result(payload)


@router.get("/uploads/{upload_id}/template-prediction", response_model=TemplatePredictionResult)
def predict_template_for_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> TemplatePredictionResult:
    upload = db.get(ReportUpload, upload_id)
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found.")
    ensure_project_read_access(db, project_id=upload.project_id, current_user=current_user)

    ml_service = MLService(db)
    payload = ml_service.analyze_upload(upload=upload)
    return _to_prediction_result(payload["prediction"])


@router.get("/tasks/{task_id}/pipeline-result", response_model=MLPipelineResult)
def get_ml_pipeline_result(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> MLPipelineResult:
    stmt = (
        select(ProcessingTask)
        .options(
            selectinload(ProcessingTask.ml_template),
            selectinload(ProcessingTask.errors),
            selectinload(ProcessingTask.report),
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    ensure_project_read_access(db, project_id=task.report.project_id, current_user=current_user)

    return _build_pipeline_result(task)


@router.post("/tasks/{task_id}/confirm-mapping", response_model=MLPipelineResult, dependencies=[Depends(require_operator_user)])
def confirm_column_mapping(
    task_id: int,
    payload: ColumnMappingConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> MLPipelineResult:
    stmt = (
        select(ProcessingTask)
        .options(
            selectinload(ProcessingTask.ml_template),
            selectinload(ProcessingTask.errors),
            selectinload(ProcessingTask.report),
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    ensure_project_write_access(db, project_id=task.report.project_id, current_user=current_user)

    params = dict(task.params_json or {})
    params["confirmed_mappings"] = [item.model_dump() for item in payload.mappings]
    params["mapping_confirmation_required"] = False
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
            selectinload(ProcessingTask.report),
        )
        .where(ProcessingTask.id == task_id)
    )
    task = db.scalar(stmt)
    return _build_pipeline_result(task)