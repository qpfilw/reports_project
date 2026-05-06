from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ScriptSecurityError(ValueError):
    """Ошибка предварительной проверки пользовательского скрипта."""


class ScriptExecutionError(RuntimeError):
    """Ошибка выполнения пользовательского скрипта."""


@dataclass(slots=True)
class ScriptRunResult:
    rows: list[dict[str, Any]]
    added_columns: list[str] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)


def validate_script_code(script_code: str, *, entrypoint: str = "process") -> None:
    if not script_code.strip():
        raise ScriptSecurityError("Код скрипта не может быть пустым.")

    try:
        compile(script_code, "<processing_script>", "exec")
    except SyntaxError as exc:
        raise ScriptSecurityError(
            f"Синтаксическая ошибка: {exc.msg} на строке {exc.lineno}."
        ) from exc

    if f"def {entrypoint}(" not in script_code:
        raise ScriptSecurityError(
            f"В расширенном скрипте должна быть объявлена функция {entrypoint}(context)."
        )


def _build_runner_code(entrypoint: str) -> str:
    return textwrap.dedent(
        f"""
        from __future__ import annotations

        import importlib.util
        import json
        import pathlib
        import sys
        import traceback


        def _json_default(value):
            try:
                import datetime
                if isinstance(value, (datetime.date, datetime.datetime)):
                    return value.isoformat()
            except Exception:
                pass
            return str(value)


        def main():
            script_path = pathlib.Path(sys.argv[1])
            input_path = pathlib.Path(sys.argv[2])
            output_path = pathlib.Path(sys.argv[3])

            with input_path.open('r', encoding='utf-8') as handle:
                context = json.load(handle)

            spec = importlib.util.spec_from_file_location('user_processing_script', script_path)
            if spec is None or spec.loader is None:
                raise RuntimeError('Не удалось загрузить пользовательский скрипт.')

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            process = getattr(module, {entrypoint!r}, None)
            if not callable(process):
                raise RuntimeError('Функция {entrypoint}(context) не найдена или не является вызываемой.')

            result = process(context)

            if isinstance(result, list):
                payload = {{'rows': result, 'summary': {{}}, 'warnings': []}}
            elif isinstance(result, dict):
                payload = result
            else:
                raise RuntimeError('Скрипт должен вернуть список строк или словарь с ключом rows.')

            if 'rows' not in payload:
                raise RuntimeError('Результат скрипта должен содержать ключ rows.')
            if not isinstance(payload['rows'], list):
                raise RuntimeError('Поле rows должно быть списком словарей.')

            output_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
                encoding='utf-8',
            )


        if __name__ == '__main__':
            try:
                main()
            except Exception:
                traceback.print_exc(file=sys.stderr)
                raise
        """
    )


def _collect_added_columns(
    *,
    original_rows: list[dict[str, Any]],
    processed_rows: list[dict[str, Any]],
) -> list[str]:
    original_columns = set(original_rows[0].keys()) if original_rows else set()
    added_columns: list[str] = []
    for row in processed_rows:
        if not isinstance(row, dict):
            continue
        for column in row.keys():
            if column not in original_columns and column not in added_columns:
                added_columns.append(column)
    return added_columns


def _normalize_warnings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, dict):
            normalized.append(
                {
                    "error_type": str(item.get("error_type") or item.get("type") or "processing_script"),
                    "error_code": str(item.get("error_code") or item.get("code") or "PROCESSING_SCRIPT_WARNING"),
                    "details": str(item.get("details") or item.get("message") or item),
                    "field_path": item.get("field_path") or item.get("field"),
                    "row_number": item.get("row_number"),
                    "source_value": item.get("source_value"),
                    "is_critical": bool(item.get("is_critical") or item.get("is_fatal") or False),
                }
            )
        else:
            normalized.append(
                {
                    "error_type": "processing_script",
                    "error_code": "PROCESSING_SCRIPT_WARNING",
                    "details": str(item),
                    "field_path": None,
                    "row_number": index,
                    "source_value": None,
                    "is_critical": False,
                }
            )
    return normalized


def run_processing_script(
    *,
    rows: list[dict[str, Any]],
    script_code: str,
    context: dict[str, Any] | None = None,
    timeout_seconds: int = 120,
    entrypoint: str = "process",
) -> ScriptRunResult:

    validate_script_code(script_code, entrypoint=entrypoint)

    payload = dict(context or {})
    payload.setdefault("rows", rows)
    payload.setdefault("params", {})

    with tempfile.TemporaryDirectory(prefix="report_script_") as temp_dir:
        temp_path = Path(temp_dir)
        script_path = temp_path / "user_script.py"
        runner_path = temp_path / "runner.py"
        input_path = temp_path / "input_context.json"
        output_path = temp_path / "output.json"
        output_dir = temp_path / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        payload["output_dir"] = str(output_dir)
        script_path.write_text(script_code, encoding="utf-8")
        runner_path.write_text(_build_runner_code(entrypoint), encoding="utf-8")
        input_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        try:
            completed = subprocess.run(
                [sys.executable, str(runner_path), str(script_path), str(input_path), str(output_path)],
                cwd=str(temp_path),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ScriptExecutionError(
                f"Пользовательский скрипт превысил лимит выполнения {timeout_seconds} секунд."
            ) from exc

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            details = stderr or stdout or f"Код завершения: {completed.returncode}"
            raise ScriptExecutionError(f"Ошибка выполнения расширенного скрипта: {details}")

        if not output_path.exists():
            raise ScriptExecutionError("Пользовательский скрипт не сформировал output.json.")

        try:
            result_payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ScriptExecutionError("Пользовательский скрипт вернул некорректный JSON-результат.") from exc

    processed_rows = result_payload.get("rows")
    if not isinstance(processed_rows, list):
        raise ScriptExecutionError("Поле rows в результате скрипта должно быть списком.")

    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(processed_rows, start=1):
        if not isinstance(row, dict):
            raise ScriptExecutionError(f"Строка результата №{index} не является словарём.")
        normalized_rows.append(row)

    added_columns = _collect_added_columns(original_rows=rows, processed_rows=normalized_rows)
    summary = result_payload.get("summary") if isinstance(result_payload.get("summary"), dict) else {}
    warnings = _normalize_warnings(result_payload.get("warnings"))
    stats = result_payload.get("stats") if isinstance(result_payload.get("stats"), dict) else {}
    stats = {
        **stats,
        "processed_rows": len(normalized_rows),
        "added_columns": added_columns,
        "added_columns_count": len(added_columns),
        "entrypoint": entrypoint,
    }
    return ScriptRunResult(
        rows=normalized_rows,
        added_columns=added_columns,
        warnings=warnings,
        stats=stats,
        summary=summary,
    )


def validate_script_with_sample(
    *,
    script_code: str,
    sample_context: dict[str, Any] | None = None,
    sample_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sample_rows = [
        sample_row
        or {
            "Итого с НДС": 350000,
            "Статус оплаты": "Ожидает оплаты",
            "Категория расходов": "IT",
        }
    ]
    context = sample_context or {
        "rows": sample_rows,
        "files": {"main": None, "additional": [], "by_role": {}},
        "params": {},
    }
    result = run_processing_script(rows=sample_rows, script_code=script_code, context=context, timeout_seconds=30)
    return {
        "is_valid": True,
        "message": "Расширенный скрипт успешно проверен на тестовом контексте.",
        "output_row": result.rows[0] if result.rows else None,
        "added_columns": result.added_columns,
        "error": None,
    }
