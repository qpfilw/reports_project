from __future__ import annotations
import json
import re
from pathlib import Path
from uuid import uuid4
from app.core.config import get_settings

_FILENAME_SANITIZER = re.compile(r"[^A-Za-z0-9._-]+")

def get_storage_root() -> Path:
    settings = get_settings()
    root = settings.storage_root_path
    root.mkdir(parents=True, exist_ok=True)
    return root

def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def sanitize_filename(filename: str) -> str:
    cleaned = _FILENAME_SANITIZER.sub("_", filename.strip())
    cleaned = cleaned.strip("._")
    return cleaned or f"file_{uuid4().hex}"

def build_upload_relative_path(report_id: int, upload_version: int, original_filename: str) -> str:
    safe_name = sanitize_filename(original_filename)
    return f"uploads/report_{report_id}/v{upload_version}/{safe_name}"

def build_normalized_relative_path(report_id: int, task_id: int) -> str:
    return f"normalized/report_{report_id}/task_{task_id}.json"

def build_export_relative_path(report_id: int, task_id: int, extension: str) -> str:
    safe_ext = extension.lower().lstrip(".")
    return f"exports/report_{report_id}/task_{task_id}.{safe_ext}"

def resolve_storage_path(relative_path: str) -> Path:
    return get_storage_root() / relative_path

def write_bytes(relative_path: str, content: bytes) -> Path:
    absolute_path = resolve_storage_path(relative_path)
    ensure_directory(absolute_path.parent)
    absolute_path.write_bytes(content)
    return absolute_path

def write_json(relative_path: str, payload: object) -> Path:
    absolute_path = resolve_storage_path(relative_path)
    ensure_directory(absolute_path.parent)
    absolute_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return absolute_path

def read_json(relative_path: str) -> object:
    absolute_path = resolve_storage_path(relative_path)
    return json.loads(absolute_path.read_text(encoding="utf-8"))

def file_size_for(relative_path: str) -> int:
    return resolve_storage_path(relative_path).stat().st_size
