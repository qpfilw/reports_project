from __future__ import annotations
from html import escape
from pathlib import Path
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from app.exporters.formatting import format_export_text


_FONT_NAME = "Helvetica"
_FONT_REGISTERED = False
logger = logging.getLogger(__name__)


def _candidate_font_paths() -> list[Path]:
    return [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]

def _ensure_unicode_font() -> str:
    global _FONT_REGISTERED, _FONT_NAME
    if _FONT_REGISTERED:
        return _FONT_NAME

    for font_path in _candidate_font_paths():
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("AppUnicode", str(font_path)))
            _FONT_NAME = "AppUnicode"
            _FONT_REGISTERED = True
            logger.info("PDF export font registered: %s", font_path)
            return _FONT_NAME
        except Exception as exc:  # pragma: no cover - defensive logging for host-specific font issues
            logger.warning("Failed to register PDF export font %s: %s", font_path, exc)

    logger.warning(
        "Unicode font for PDF export was not found. Falling back to %s; Cyrillic text may render incorrectly.",
        _FONT_NAME,
    )
    _FONT_REGISTERED = True
    return _FONT_NAME


def export_processing_summary_to_pdf(
    path: str | Path,
    *,
    report_title: str,
    task_id: int,
    summary: dict[str, object],
    preview_rows: list[dict[str, object]],
) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    font_name = _ensure_unicode_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleUnicode",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=16,
        leading=20,
        spaceAfter=10,
    )
    normal_style = ParagraphStyle(
        name="NormalUnicode",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=12,
        spaceAfter=4,
    )
    table_style_text = ParagraphStyle(
        name="TableUnicode",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8,
        leading=10,
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story: list[object] = [
        Paragraph(f"Отчет: {escape(report_title)}", title_style),
        Paragraph(f"Задача обработки: {task_id}", normal_style),
        Paragraph(f"Строк: {summary.get('total_rows', 0)}", normal_style),
        Paragraph(f"Предупреждения: {summary.get('warnings', 0)}", normal_style),
        Paragraph(f"Ошибки: {summary.get('errors', 0)}", normal_style),
        Spacer(1, 6),
        Paragraph("Предпросмотр данных", normal_style),
        Spacer(1, 4),
    ]

    if preview_rows:
        headers = list(preview_rows[0].keys())
        table_data = [
            [Paragraph(escape(str(header)), table_style_text) for header in headers]
        ]
        for row in preview_rows[:20]:
            table_data.append(
                [Paragraph(escape(format_export_text(row.get(header))), table_style_text) for header in headers]
            )

        col_width = document.width / max(len(headers), 1)
        table = Table(table_data, colWidths=[col_width] * len(headers), repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEADING", (0, 0), (-1, -1), 10),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("Нет данных для предпросмотра.", normal_style))

    document.build(story)
