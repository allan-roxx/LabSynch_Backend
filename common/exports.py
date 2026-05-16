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
    Image,
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ── Beaker icon ────────────────────────────────────────────────────────────────

def _beaker_png_buf(size: int = 56) -> io.BytesIO:
    """Generate a simple beaker icon PNG using Pillow and return as BytesIO."""
    from PIL import Image as PilImage, ImageDraw

    s = size
    img = PilImage.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    blue = (37, 99, 235, 255)
    lblue = (147, 197, 253, 180)

    # Neck rim
    draw.rectangle([int(s * .30), int(s * .05), int(s * .70), int(s * .11)], fill=blue)
    # Neck shaft
    draw.rectangle([int(s * .37), int(s * .11), int(s * .63), int(s * .32)], fill=blue)
    # Body (trapezoid)
    draw.polygon([
        (int(s * .37), int(s * .32)),
        (int(s * .63), int(s * .32)),
        (int(s * .86), int(s * .88)),
        (int(s * .14), int(s * .88)),
    ], fill=blue)
    # Liquid highlight
    draw.polygon([
        (int(s * .41), int(s * .56)),
        (int(s * .59), int(s * .56)),
        (int(s * .82), int(s * .86)),
        (int(s * .18), int(s * .86)),
    ], fill=lblue)
    # Base ellipse
    draw.ellipse([int(s * .14), int(s * .84), int(s * .86), int(s * .96)], fill=blue)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# ── CSV ────────────────────────────────────────────────────────────────────────

class _EchoBuffer:
    """A write-only file-like object that echoes the value written."""
    def write(self, value):
        return value


def export_csv(headers: list[str], rows: list[dict], filename_stem: str) -> StreamingHttpResponse:
    """
    Return a StreamingHttpResponse that downloads a CSV file.

    :param headers:       Ordered list of column labels.
    :param rows:          List of dicts keyed by those labels.
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


# ── PDF ────────────────────────────────────────────────────────────────────────

_STYLES = getSampleStyleSheet()

_COMPANY_STYLE = ParagraphStyle(
    "ExportCompany",
    parent=_STYLES["Normal"],
    fontSize=13,
    fontName="Helvetica-Bold",
    textColor=colors.HexColor("#1e3a5f"),
    alignment=1,  # CENTER
    spaceAfter=1,
)
_TITLE_STYLE = ParagraphStyle(
    "ExportTitle",
    parent=_STYLES["Normal"],
    fontSize=11,
    fontName="Helvetica",
    textColor=colors.HexColor("#374151"),
    alignment=1,
    spaceAfter=1,
)
_DATE_STYLE = ParagraphStyle(
    "ExportDate",
    parent=_STYLES["Normal"],
    fontSize=7,
    textColor=colors.HexColor("#9ca3af"),
    alignment=1,
)
_SMALL = ParagraphStyle("Small", parent=_STYLES["Normal"], fontSize=7)

_HEADER_BG  = colors.HexColor("#1e3a5f")
_ROW_ALT_BG = colors.HexColor("#f0f4f8")
_ACCENT     = colors.HexColor("#2563eb")


def _canvas_footer(canvas, doc):
    """Draw a thin footer line + page number on every page."""
    canvas.saveState()
    w, _h = doc.pagesize
    canvas.setStrokeColor(colors.HexColor("#d1d5db"))
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, 1.1 * cm, w - 1.5 * cm, 1.1 * cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#9ca3af"))
    canvas.drawString(1.5 * cm, 0.65 * cm, "LabSynch Equipment Services — Confidential")
    canvas.drawRightString(w - 1.5 * cm, 0.65 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _header_elements(title: str, datestamp: str, page_width: float) -> list:
    """Return the branded report header as a list of reportlab flowables."""
    try:
        beaker_buf = _beaker_png_buf(52)
        beaker_img = Image(beaker_buf, width=0.9 * cm, height=0.9 * cm)
    except Exception:
        beaker_img = Spacer(0.9 * cm, 0.9 * cm)

    center_block = [
        Paragraph("LabSynch Equipment Services", _COMPANY_STYLE),
        Paragraph(title, _TITLE_STYLE),
        Paragraph(f"Generated: {datestamp}", _DATE_STYLE),
    ]

    avail = page_width - 3 * cm
    header_table = Table(
        [[beaker_img, center_block, Spacer(1, 1)]],
        colWidths=[1.2 * cm, avail - 1.2 * cm, 0.01 * cm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    return [
        header_table,
        HRFlowable(width="100%", thickness=1.5, color=_ACCENT, spaceAfter=6),
        Spacer(1, 4),
    ]


def export_pdf(title: str, headers: list[str], rows: list[dict], filename_stem: str) -> HttpResponse:
    """
    Return an HttpResponse that downloads a PDF table.

    :param title:         Document title shown in the page header.
    :param headers:       Ordered list of column labels.
    :param rows:          List of dicts keyed by those labels.
    :param filename_stem: Base file name without extension.
    """
    buf = io.BytesIO()
    page_size = landscape(A4) if len(headers) > 6 else A4
    doc = SimpleDocTemplate(
        buf,
        pagesize=page_size,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    datestamp = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
    page_width = page_size[0]

    elements = _header_elements(title, datestamp, page_width)

    # Table
    usable_width = page_width - 3 * cm
    col_width = usable_width / len(headers)

    table_data = [[Paragraph(f"<b>{h}</b>", _SMALL) for h in headers]]
    for row in rows:
        table_data.append([
            Paragraph(str(row.get(h, "") or ""), _SMALL) for h in headers
        ])

    table = Table(table_data, colWidths=[col_width] * len(headers), repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  _HEADER_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("FONTSIZE",      (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, _ROW_ALT_BG]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.Color(0.82, 0.82, 0.82)),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)

    doc.build(elements, onFirstPage=_canvas_footer, onLaterPages=_canvas_footer)
    buf.seek(0)

    datestamp_file = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = f"{filename_stem}_{datestamp_file}.pdf"
    response = HttpResponse(buf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
