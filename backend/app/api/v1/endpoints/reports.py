from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_approved_user, require_manager_user, require_operator_user
from app.core.access import (
    apply_project_scope,
    ensure_project_read_access,
    ensure_project_write_access,
    ensure_template_matches_report_type,
    ensure_user_has_project_membership,
    is_admin,
)
from app.models.enums import AuditActionEnum, AuditEntityTypeEnum, ReportStatusEnum
from app.models.ml_template import MlTemplate
from app.models.project import Project
from app.models.report import Report
from app.models.report_type import ReportType
from app.models.report_upload import ReportUpload
from app.models.user import User
from app.schemas.report import (
    ReportCreate,
    ReportDetailRead,
    ReportRead,
    ReportStatusUpdate,
    ReportUpdate,
    ReportWorkflowActionRequest,
)
from app.schemas.upload import ReportUploadDetailRead
from app.services.report_service import ReportService
from app.services.upload_service import UploadService
from app.services.audit_service import log_audit, snapshot_report, snapshot_report_upload

router = APIRouter(dependencies=[Depends(require_approved_user)])


MANAGER_ONLY_REPORT_STATUSES = {
    ReportStatusEnum.ON_APPROVAL,
    ReportStatusEnum.APPROVED,
    ReportStatusEnum.REJECTED,
    ReportStatusEnum.ARCHIVED,
}


def _get_report_detail_or_404(db: Session, report_id: int) -> Report:
    stmt = (
        select(Report)
        .options(
            selectinload(Report.report_type),
            selectinload(Report.creator),
            selectinload(Report.current_assignee),
            selectinload(Report.approver),
            selectinload(Report.ml_template),
        )
        .where(Report.id == report_id)
    )
    report = db.scalar(stmt)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


def _get_report_for_update_or_404(db: Session, report_id: int, current_user: User) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    ensure_project_write_access(db, project_id=report.project_id, current_user=current_user)
    return report


def _validate_related_users(
    db: Session,
    *,
    project_id: int,
    current_assignee_id: int | None = None,
    approver_id: int | None = None,
) -> None:
    if current_assignee_id is not None:
        if db.get(User, current_assignee_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found.")
        ensure_user_has_project_membership(db, project_id=project_id, user_id=current_assignee_id)
    if approver_id is not None:
        if db.get(User, approver_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approver user not found.")
        ensure_user_has_project_membership(db, project_id=project_id, user_id=approver_id)


@router.get("/", response_model=list[ReportRead])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> list[Report]:
    stmt = apply_project_scope(select(Report), project_column=Report.project_id, current_user=current_user)
    stmt = stmt.order_by(Report.id)
    return list(db.scalars(stmt).all())


@router.get("/{report_id}", response_model=ReportDetailRead)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_approved_user),
) -> Report:
    report = _get_report_detail_or_404(db, report_id)
    ensure_project_read_access(db, project_id=report.project_id, current_user=current_user)
    return report


@router.post("/", response_model=ReportDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_operator_user)])
def create_report(
    payload: ReportCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> Report:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    ensure_project_write_access(db, project_id=payload.project_id, current_user=current_user)

    report_type = db.get(ReportType, payload.report_type_id)
    if report_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")

    creator = db.get(User, payload.creator_id)
    if creator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator user not found.")

    if not is_admin(current_user) and payload.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can create reports only on your own behalf.",
        )

    _validate_related_users(
        db,
        project_id=payload.project_id,
        current_assignee_id=payload.current_assignee_id,
        approver_id=payload.approver_id,
    )

    if payload.ml_template_id is not None:
        ml_template = db.get(MlTemplate, payload.ml_template_id)
        if ml_template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ML template not found.")
        ensure_template_matches_report_type(template=ml_template, report_type_id=payload.report_type_id)

    report = Report(**payload.model_dump())
    db.add(report)
    db.flush()
    log_audit(
        db,
        action=AuditActionEnum.CREATE,
        entity_type=AuditEntityTypeEnum.REPORT,
        entity_id=report.id,
        actor=current_user,
        project_id=report.project_id,
        after_json={"event": "report_created", **(snapshot_report(report) or {})},
        request=request,
    )
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post(
    "/{report_id}/uploads/file",
    response_model=ReportUploadDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operator_user)],
)
def upload_report_file(
    report_id: int,
    file: UploadFile = File(...),
    comment: str | None = Form(default=None),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
):
    report = _get_report_detail_or_404(db, report_id)
    ensure_project_write_access(db, project_id=report.project_id, current_user=current_user)

    service = UploadService(db)
    upload = service.create_report_upload(
        report_id=report_id,
        upload_file=file,
        uploaded_by=current_user,
        comment=comment,
    )
    log_audit(
        db,
        action=AuditActionEnum.CREATE,
        entity_type=AuditEntityTypeEnum.REPORT_UPLOAD,
        entity_id=upload.id,
        actor=current_user,
        project_id=report.project_id,
        after_json={"event": "report_uploaded", **(snapshot_report_upload(upload) or {})},
        request=request,
    )
    db.commit()
    stmt = (
        select(ReportUpload)
        .options(
            selectinload(ReportUpload.report),
            selectinload(ReportUpload.report_type),
            selectinload(ReportUpload.uploader),
        )
        .where(ReportUpload.id == upload.id)
    )
    return db.scalar(stmt)


@router.patch("/{report_id}", response_model=ReportDetailRead, dependencies=[Depends(require_operator_user)])
def update_report(
    report_id: int,
    payload: ReportUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)

    data = payload.model_dump(exclude_unset=True)
    before_report = snapshot_report(report)

    if "report_type_id" in data and data["report_type_id"] is not None:
        if db.get(ReportType, data["report_type_id"]) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report type not found.")

    _validate_related_users(
        db,
        project_id=report.project_id,
        current_assignee_id=data.get("current_assignee_id"),
        approver_id=data.get("approver_id"),
    )

    if "ml_template_id" in data and data["ml_template_id"] is not None:
        ml_template = db.get(MlTemplate, data["ml_template_id"])
        if ml_template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ML template not found.")
        report_type_id = data.get("report_type_id", report.report_type_id)
        ensure_template_matches_report_type(template=ml_template, report_type_id=report_type_id)

    for field, value in data.items():
        setattr(report, field, value)

    if data:
        log_audit(db, action=AuditActionEnum.UPDATE, entity_type=AuditEntityTypeEnum.REPORT, entity_id=report.id, actor=current_user, project_id=report.project_id, before_json=before_report, after_json={"event": "report_updated", **(snapshot_report(report) or {})}, request=request)

    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.patch("/{report_id}/status", response_model=ReportDetailRead, dependencies=[Depends(require_operator_user)])
def update_report_status(
    report_id: int,
    payload: ReportStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)

    before_report = snapshot_report(report)
    target_status = ReportStatusEnum(payload.status)
    if target_status in MANAGER_ONLY_REPORT_STATUSES:
        require_manager_user(current_user)

    _validate_related_users(
        db,
        project_id=report.project_id,
        current_assignee_id=payload.current_assignee_id,
        approver_id=payload.approver_id,
    )

    service = ReportService(db)
    service.transition_report_status(
        report,
        target_status=target_status,
        comment=payload.last_comment,
        current_assignee_id=payload.current_assignee_id,
        approver_id=payload.approver_id,
    )
    log_audit(
        db,
        action=AuditActionEnum.UPDATE,
        entity_type=AuditEntityTypeEnum.REPORT,
        entity_id=report.id,
        actor=current_user,
        project_id=report.project_id,
        before_json=before_report,
        after_json={"event": "report_status_updated", "target_status": payload.status, **(snapshot_report(report) or {})},
        request=request,
    )
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post("/{report_id}/unarchive", response_model=ReportDetailRead, dependencies=[Depends(require_manager_user)])
def unarchive_report(
    report_id: int,
    payload: ReportWorkflowActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)
    before_report = snapshot_report(report)

    service = ReportService(db)
    service.unarchive(report, comment=payload.last_comment)
    log_audit(
        db,
        action=AuditActionEnum.UPDATE,
        entity_type=AuditEntityTypeEnum.REPORT,
        entity_id=report.id,
        actor=current_user,
        project_id=report.project_id,
        before_json=before_report,
        after_json={"event": "report_unarchived", **(snapshot_report(report) or {})},
        request=request,
    )
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post("/{report_id}/submit-review", response_model=ReportDetailRead, dependencies=[Depends(require_operator_user)])
def submit_report_for_review(
    report_id: int,
    payload: ReportWorkflowActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)
    before_report = snapshot_report(report)
    _validate_related_users(db, project_id=report.project_id, current_assignee_id=payload.current_assignee_id)

    service = ReportService(db)
    service.submit_for_review(
        report,
        comment=payload.last_comment,
        current_assignee_id=payload.current_assignee_id,
    )
    log_audit(db, action=AuditActionEnum.SUBMIT, entity_type=AuditEntityTypeEnum.REPORT, entity_id=report.id, actor=current_user, project_id=report.project_id, before_json=before_report, after_json={"event": "report_submitted_for_review", **(snapshot_report(report) or {})}, request=request)
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post("/{report_id}/submit-approval", response_model=ReportDetailRead, dependencies=[Depends(require_manager_user)])
def submit_report_for_approval(
    report_id: int,
    payload: ReportWorkflowActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)
    before_report = snapshot_report(report)
    _validate_related_users(db, project_id=report.project_id, approver_id=payload.approver_id)

    service = ReportService(db)
    service.submit_for_approval(
        report,
        comment=payload.last_comment,
        approver_id=payload.approver_id,
    )
    log_audit(db, action=AuditActionEnum.SUBMIT, entity_type=AuditEntityTypeEnum.REPORT, entity_id=report.id, actor=current_user, project_id=report.project_id, before_json=before_report, after_json={"event": "report_submitted_for_approval", **(snapshot_report(report) or {})}, request=request)
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post("/{report_id}/approve", response_model=ReportDetailRead, dependencies=[Depends(require_manager_user)])
def approve_report(
    report_id: int,
    payload: ReportWorkflowActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)
    before_report = snapshot_report(report)
    service = ReportService(db)
    service.approve(report, comment=payload.last_comment)
    log_audit(db, action=AuditActionEnum.APPROVE, entity_type=AuditEntityTypeEnum.REPORT, entity_id=report.id, actor=current_user, project_id=report.project_id, before_json=before_report, after_json={"event": "report_approved", **(snapshot_report(report) or {})}, request=request)
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post("/{report_id}/reject", response_model=ReportDetailRead, dependencies=[Depends(require_manager_user)])
def reject_report(
    report_id: int,
    payload: ReportWorkflowActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)
    before_report = snapshot_report(report)
    service = ReportService(db)
    service.reject(report, comment=payload.last_comment)
    log_audit(db, action=AuditActionEnum.REJECT, entity_type=AuditEntityTypeEnum.REPORT, entity_id=report.id, actor=current_user, project_id=report.project_id, before_json=before_report, after_json={"event": "report_rejected", **(snapshot_report(report) or {})}, request=request)
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)


@router.post("/{report_id}/rework", response_model=ReportDetailRead, dependencies=[Depends(require_operator_user)])
def send_report_to_rework(
    report_id: int,
    payload: ReportWorkflowActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_user),
) -> Report:
    report = _get_report_for_update_or_404(db, report_id, current_user)
    before_report = snapshot_report(report)
    service = ReportService(db)
    service.send_to_rework(report, comment=payload.last_comment)
    log_audit(
        db,
        action=AuditActionEnum.UPDATE,
        entity_type=AuditEntityTypeEnum.REPORT,
        entity_id=report.id,
        actor=current_user,
        project_id=report.project_id,
        before_json=before_report,
        after_json={"event": "report_sent_to_rework", **(snapshot_report(report) or {})},
        request=request,
    )
    db.commit()
    db.refresh(report)
    return _get_report_detail_or_404(db, report.id)