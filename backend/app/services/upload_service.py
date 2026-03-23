from __future__ import annotations
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.report import Report
from app.models.report_upload import ReportUpload
from app.models.user import User
from app.services.report_service import ReportService
from app.utils.file_hash import sha256_for_file
from app.utils.storage import build_upload_relative_path, resolve_storage_path

ALLOWED_UPLOAD_EXTENSIONS = {".csv", ".xlsx"}

class UploadService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.report_service = ReportService(db)

    def create_report_upload(
        self,
        *,
        report_id: int,
        upload_file: UploadFile,
        uploaded_by: User,
        comment: str | None = None,
    ) -> ReportUpload:
        report = self.db.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

        if not upload_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")

        suffix = Path(upload_file.filename).suffix.lower()
        if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV and XLSX files are supported.",
            )

        upload_version = self._get_next_upload_version(report_id=report_id)
        relative_path = build_upload_relative_path(
            report_id=report_id,
            upload_version=upload_version,
            original_filename=upload_file.filename,
        )
        absolute_path = resolve_storage_path(relative_path)
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            file_size = self._save_upload_file(upload_file=upload_file, destination=absolute_path)
            self._validate_upload_size(file_size)
            checksum = sha256_for_file(absolute_path)

            self._mark_previous_uploads_not_latest(report_id=report_id)

            upload = ReportUpload(
                report_id=report.id,
                project_id=report.project_id,
                report_type_id=report.report_type_id,
                uploaded_by=uploaded_by.id,
                original_filename=upload_file.filename,
                storage_path=relative_path,
                content_type=upload_file.content_type,
                file_size=file_size,
                checksum_sha256=checksum,
                is_latest=True,
                upload_version=upload_version,
                comment=comment,
            )
            self.db.add(upload)
            self.db.flush()
            self.report_service.mark_uploaded(
                report,
                upload_version=upload.upload_version,
                comment=comment or f"Загружена версия файла №{upload.upload_version}.",
            )
            self.db.commit()
            self.db.refresh(upload)
            return upload
        except Exception:
            if absolute_path.exists():
                absolute_path.unlink(missing_ok=True)
            raise

    def _get_next_upload_version(self, *, report_id: int) -> int:
        current_max = self.db.scalar(
            select(func.max(ReportUpload.upload_version)).where(ReportUpload.report_id == report_id)
        )
        return int(current_max or 0) + 1

    def _mark_previous_uploads_not_latest(self, *, report_id: int) -> None:
        stmt = select(ReportUpload).where(
            ReportUpload.report_id == report_id,
            ReportUpload.is_latest.is_(True),
        )
        for existing_upload in self.db.scalars(stmt).all():
            existing_upload.is_latest = False

    @staticmethod
    def _save_upload_file(*, upload_file: UploadFile, destination: Path) -> int:
        size = 0
        upload_file.file.seek(0)
        with destination.open("wb") as output_file:
            while chunk := upload_file.file.read(1024 * 1024):
                output_file.write(chunk)
                size += len(chunk)
        upload_file.file.seek(0)
        return size

    def _validate_upload_size(self, file_size: int) -> None:
        max_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File is too large. Maximum allowed size is {self.settings.max_upload_size_mb} MB.",
            )