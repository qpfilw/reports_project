from __future__ import annotations

import csv
from pathlib import Path

from app.exporters.formatting import format_export_value

def export_rows_to_csv(path: str | Path, rows: list[dict[str, object]]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    headers = list(rows[0].keys()) if rows else []
    with file_path.open("w", encoding="utf-8-sig", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=headers)
        if headers:
            writer.writeheader()
            for row in rows:
                writer.writerow({header: format_export_value(row.get(header)) for header in headers})
