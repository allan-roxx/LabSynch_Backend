"""
Shared export utilities: CSV (StreamingHttpResponse) and PDF (FileResponse).

Usage from a viewset action:
    from common.exports import export_csv, export_pdf

    rows = [
        {"Reference": "BK-2025-0001", "Status": "PAID", ...},
        ...
    ]
    headers = ["Reference", "Status", ...]

    if fmt == "pdf":
        return export_pdf("Bookings Report", headers, rows, "bookings")
    return export_csv(headers, rows, "bookings")
"""

import io
import csv
from datetime import datetime

from django.http import HttpResponse, StreamingHttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)



# CSV


class _EchoBuffer:
    """A write-only file-like object that returns the value written."""
    def write(self, value):
        return value


def export_csv(headers: list[str], rows: list[dict], filename_stem: str) -> StreamingHttpResponse:
    """
    Return a StreamingHttpResponse that downloads a CSV file.

    :param headers:  Ordered list of column labels.
    :param rows:     List of dicts keyed by those labels.
    :param filename_stem: Base file name without extension, e.g. "bookings".
    """
    pseudo_buffer = _EchoBuffer()
    writer = csv.DictWriter(pseudo_buffer, fieldnames=headers)

    def generate():
        yield writer.writeheader()
        for row in rows:
            yield writer.writerow(row)

    datestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = f"{filename_stem}_{datestamp}.csv"
    response = StreamingHttpResponse(generate(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response



# PDF


_STYLES = getSampleStyleSheet()
_TITLE_STYLE = ParagraphStyle("ExportTitle", parent=_STYLES["Title"], fontSize=16, spaceAfter=8)
_NORMAL = _STYLES["Normal"]
_SMALL = ParagraphStyle("Small", parent=_STYLES["Normal"], fontSize=7)

_HEADER_BG = colors.HexColor("#1a3c5e")
_ROW_ALT_BG = colors.HexColor("#f2f6fb")


def export_pdf(title: str, headers: list[str], rows: list[dict], filename_stem: str) -> HttpResponse:
    """
    Return an HttpResponse that downloads a PDF table.

    :param title:        Document title shown at the top of the PDF.
    :param headers:      Ordered list of column labels.
    :param rows:         List of dicts keyed by those labels.
    :param filename_stem: Base file name without extension.
    """
    buf = io.BytesIO()
    page_size = landscape(A4) if len(headers) > 6 else A4
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    elements = []

    # Title block
    datestamp = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
    elements.append(Paragraph("<b>LabSynch Equipment Services</b>", _NORMAL))
    elements.append(Paragraph(title, _TITLE_STYLE))
    elements.append(Paragraph(f"Generated: {datestamp}", _NORMAL))
    elements.append(Spacer(1, 12))

    # Table
    col_count = len(headers)
    page_width = (page_size[0] - 3 * cm)  # usable width
    col_width = page_width / col_count

    table_data = [[Paragraph(f"<b>{h}</b>", _SMALL) for h in headers]]
    for row in rows:
        table_data.append([
            Paragraph(str(row.get(h, "") or ""), _SMALL) for h in headers
        ])

    table = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        # Data rows
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT_BG]),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.4, colors.Color(0.75, 0.75, 0.75)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    doc.build(elements)
    buf.seek(0)

    datestamp_file = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = f"{filename_stem}_{datestamp_file}.pdf"
    response = HttpResponse(buf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
