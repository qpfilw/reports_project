from __future__ import annotations
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font
from app.exporters.formatting import excel_cell_value_and_format

def export_rows_to_xlsx(path: str | Path, rows: list[dict[str, object]]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "NormalizedData"

    if rows:
        headers = list(rows[0].keys())
        worksheet.append(headers)
        for cell in worksheet[1]:
            cell.font = Font(bold=True)

        for row in rows:
            worksheet.append([row.get(header) for header in headers])

        for row_index, row in enumerate(rows, start=2):
            for column_index, header in enumerate(headers, start=1):
                cell = worksheet.cell(row=row_index, column=column_index)
                export_value, number_format = excel_cell_value_and_format(row.get(header))
                cell.value = export_value
                if number_format:
                    cell.number_format = number_format

        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                cell_value = "" if cell.value is None else str(cell.value)
                max_length = max(max_length, len(cell_value))
            worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 12), 40)

    workbook.save(file_path)
    workbook.close()
