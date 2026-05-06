from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_approved_user, require_manager_user
from app.models.processing_script import ProcessingScript
from app.models.report_type import ReportType
from app.models.user import User
from app.processors.script_runner import validate_script_with_sample, validate_script_code
from app.schemas.processing_script import (
    ProcessingScriptCreate,
    ProcessingScriptDetailRead,
    ProcessingScriptRead,
    ProcessingScriptUpdate,
    ProcessingScriptValidateRequest,
    ProcessingScriptValidateResponse,
)

router = APIRouter(dependencies=[Depends(require_approved_user)])


def _get_script_detail_or_404(db: Session, script_id: int) -> ProcessingScript:
    stmt = (
        select(ProcessingScript)
        .options(selectinload(ProcessingScript.creator))
        .where(ProcessingScript.id == script_id)
    )
    script = db.scalar(stmt)
    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing script not found.")
    return script


def _ensure_related_entities(db: Session, *, target_report_type_id: int | None, created_by: int | None) -> None:
    if target_report_type_id is not None and db.get(ReportType, target_report_type_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target report type not found.")
    if created_by is not None and db.get(User, created_by) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator user not found.")


def _ensure_unique_code_version(
    db: Session,
    *,
    code: str,
    version: str,
    exclude_id: int | None = None,
) -> None:
    stmt = select(ProcessingScript).where(
        ProcessingScript.code == code,
        ProcessingScript.version == version,
    )
    if exclude_id is not None:
        stmt = stmt.where(ProcessingScript.id != exclude_id)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Processing script with this code and version already exists.",
        )


def _reset_default_script(db: Session, *, target_report_type_id: int | None, exclude_id: int | None = None) -> None:
    if target_report_type_id is None:
        return
    stmt = select(ProcessingScript).where(
        ProcessingScript.target_report_type_id == target_report_type_id,
        ProcessingScript.is_default.is_(True),
    )
    if exclude_id is not None:
        stmt = stmt.where(ProcessingScript.id != exclude_id)
    for script in db.scalars(stmt).all():
        script.is_default = False


@router.get("/", response_model=list[ProcessingScriptRead])
def list_processing_scripts(db: Session = Depends(get_db)) -> list[ProcessingScript]:
    stmt = select(ProcessingScript).order_by(ProcessingScript.id)
    return list(db.scalars(stmt).all())


@router.get("/{script_id}", response_model=ProcessingScriptDetailRead)
def get_processing_script(script_id: int, db: Session = Depends(get_db)) -> ProcessingScript:
    return _get_script_detail_or_404(db, script_id)


@router.post(
    "/validate",
    response_model=ProcessingScriptValidateResponse,
    dependencies=[Depends(require_manager_user)],
)
def validate_processing_script(payload: ProcessingScriptValidateRequest) -> dict[str, object]:
    try:
        return validate_script_with_sample(
            script_code=payload.script_code,
            sample_context=payload.sample_context,
            sample_row=payload.sample_row,
        )
    except Exception as exc:  # noqa: BLE001 - validation endpoint must return user-readable error
        return {
            "is_valid": False,
            "message": "Скрипт не прошёл проверку.",
            "output_row": None,
            "added_columns": [],
            "error": str(exc),
        }


@router.post(
    "/",
    response_model=ProcessingScriptDetailRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager_user)],
)
def create_processing_script(
    payload: ProcessingScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager_user),
) -> ProcessingScript:
    _ensure_unique_code_version(db, code=payload.code, version=payload.version)
    _ensure_related_entities(
        db,
        target_report_type_id=payload.target_report_type_id,
        created_by=payload.created_by,
    )

    try:
        validation_result = validate_script_with_sample(script_code=payload.script_code)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if payload.is_default:
        _reset_default_script(db, target_report_type_id=payload.target_report_type_id)

    data = payload.model_dump()
    data["validation_json"] = validation_result
    if data.get("created_by") is None:
        data["created_by"] = current_user.id
    script = ProcessingScript(**data)
    db.add(script)
    db.commit()
    db.refresh(script)
    return _get_script_detail_or_404(db, script.id)


@router.patch(
    "/{script_id}",
    response_model=ProcessingScriptDetailRead,
    dependencies=[Depends(require_manager_user)],
)
def update_processing_script(
    script_id: int,
    payload: ProcessingScriptUpdate,
    db: Session = Depends(get_db),
) -> ProcessingScript:
    script = db.get(ProcessingScript, script_id)
    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processing script not found.")

    data = payload.model_dump(exclude_unset=True)
    new_code = data.get("code", script.code)
    new_version = data.get("version", script.version)
    _ensure_unique_code_version(db, code=new_code, version=new_version, exclude_id=script_id)

    target_report_type_id = data.get("target_report_type_id", script.target_report_type_id)
    created_by = data.get("created_by", script.created_by)
    _ensure_related_entities(db, target_report_type_id=target_report_type_id, created_by=created_by)

    if "script_code" in data:
        try:
            data["validation_json"] = validate_script_with_sample(script_code=data["script_code"])
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if data.get("is_default") is True:
        _reset_default_script(db, target_report_type_id=target_report_type_id, exclude_id=script_id)

    for field, value in data.items():
        setattr(script, field, value)

    db.commit()
    db.refresh(script)
    return _get_script_detail_or_404(db, script.id)
