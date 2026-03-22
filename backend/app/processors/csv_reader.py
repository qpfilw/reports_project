from __future__ import annotations
import csv
from pathlib import Path

DEFAULT_ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1251", "latin-1")

def read_csv_rows(path: str | Path) -> list[dict[str, object]]:
    file_path = Path(path)
    last_error: Exception | None = None

    for encoding in DEFAULT_ENCODING_CANDIDATES:
        try:
            with file_path.open("r", encoding=encoding, newline="") as file_handle:
                sample = file_handle.read(4096)
                file_handle.seek(0)
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|") if sample else csv.excel
                reader = csv.DictReader(file_handle, dialect=dialect)
                return [dict(row) for row in reader]
        except UnicodeDecodeError as exc:
            last_error = exc
        except csv.Error:
            with file_path.open("r", encoding=encoding, newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                return [dict(row) for row in reader]

    if last_error is not None:
        raise ValueError("Не удалось определить кодировку CSV-файла.") from last_error

    return []
