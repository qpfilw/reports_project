from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_approved_user, require_manager_user
from app.models.enums import AuditActionEnum, AuditEntityTypeEnum
from app.models.ml_template import MlTemplate
from app.models.processing_script import ProcessingScript
from app.models.report_type import ReportType
from app.models.user import User
from app.schemas.template import (
    MlTemplateCreate,
    MlTemplateDetailRead,
    MlTemplateRead,
    MlTemplateUpdate,
)
from app.services.audit_service import log_audit, snapshot_template

router = APIRouter(dependencies=[Depends(require_approved_user)])

def _get_template_detail_or_404(db: Session, template_id: int) -> MlTemplate:
    stmt = (
        select(MlTemplate)
        .options(selectinload(MlTemplate.creator))
        .where(MlTemplate.id == template_id)
    )
    template = db.scalar(stmt)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")
    return template

@router.get("/", response_model=list[MlTemplateRead])
def list_templates(db: Session = Depends(get_db)) -> list[MlTemplate]:
    stmt = select(MlTemplate).order_by(MlTemplate.id)
    return list(db.scalars(stmt).all())

@router.get("/{template_id}", response_model=MlTemplateDetailRead)
def get_template(template_id: int, db: Session = Depends(get_db)) -> MlTemplate:
    return _get_template_detail_or_404(db, template_id)

@router.post("/", response_model=MlTemplateDetailRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_manager_user)])
def create_template(payload: MlTemplateCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_manager_user)) -> MlTemplate:
    existing = db.scalar(
        select(MlTemplate).where(
            MlTemplate.code == payload.code,
            MlTemplate.version == payload.version,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Template with this code and version already exists.",
        )

    if payload.target_report_type_id is not None:
        report_type = db.get(ReportType, payload.target_report_type_id)
        if report_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target report type not found.",
            )

    if payload.processing_script_id is not None:
        processing_script = db.get(ProcessingScript, payload.processing_script_id)
        if processing_script is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing script not found.",
            )
        if not processing_script.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Processing script is inactive.",
            )

    if payload.created_by is not None:
        creator = db.get(User, payload.created_by)
        if creator is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Creator user not found.",
            )

    if payload.is_default and payload.target_report_type_id is not None:
        stmt = select(MlTemplate).where(
            MlTemplate.target_report_type_id == payload.target_report_type_id,
            MlTemplate.is_default.is_(True),
        )
        existing_default = db.scalar(stmt)
        if existing_default is not None:
            existing_default.is_default = False

    template = MlTemplate(**payload.model_dump())
    db.add(template)
    db.flush()
    log_audit(db, action=AuditActionEnum.CREATE, entity_type=AuditEntityTypeEnum.TEMPLATE, entity_id=template.id, actor=current_user, after_json={"event": "template_created", **(snapshot_template(template) or {})}, request=request)
    db.commit()
    db.refresh(template)
    return _get_template_detail_or_404(db, template.id)

@router.patch("/{template_id}", response_model=MlTemplateDetailRead, dependencies=[Depends(require_manager_user)])
def update_template(
    template_id: int,
    payload: MlTemplateUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> MlTemplate:
    template = db.get(MlTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")

    data = payload.model_dump(exclude_unset=True)
    before_template = snapshot_template(template)

    new_code = data.get("code", template.code)
    new_version = data.get("version", template.version)

    existing = db.scalar(
        select(MlTemplate).where(
            MlTemplate.code == new_code,
            MlTemplate.version == new_version,
            MlTemplate.id != template_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Template with this code and version already exists.",
        )

    if "target_report_type_id" in data and data["target_report_type_id"] is not None:
        report_type = db.get(ReportType, data["target_report_type_id"])
        if report_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target report type not found.",
            )

    if "processing_script_id" in data and data["processing_script_id"] is not None:
        processing_script = db.get(ProcessingScript, data["processing_script_id"])
        if processing_script is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing script not found.",
            )
        if not processing_script.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Processing script is inactive.",
            )

    target_report_type_id = data.get("target_report_type_id", template.target_report_type_id)
    is_default = data.get("is_default", template.is_default)

    if is_default and target_report_type_id is not None:
        stmt = select(MlTemplate).where(
            MlTemplate.target_report_type_id == target_report_type_id,
            MlTemplate.is_default.is_(True),
            MlTemplate.id != template_id,
        )
        existing_default = db.scalar(stmt)
        if existing_default is not None:
            existing_default.is_default = False

    for field, value in data.items():
        setattr(template, field, value)

    if data:
        log_audit(db, action=AuditActionEnum.UPDATE, entity_type=AuditEntityTypeEnum.TEMPLATE, entity_id=template.id, actor=current_user, before_json=before_template, after_json={"event": "template_updated", **(snapshot_template(template) or {})}, request=request)

    db.commit()
    db.refresh(template)
    return _get_template_detail_or_404(db, template.id)