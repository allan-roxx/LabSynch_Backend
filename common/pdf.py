"""
PDF generation utilities for receipts and equipment usage contracts.
Uses reportlab to render documents on-the-fly.
"""

import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

_STYLES = getSampleStyleSheet()
_TITLE = ParagraphStyle("DocTitle", parent=_STYLES["Title"], fontSize=18, spaceAfter=10)
_HEADING = ParagraphStyle("SectionHeading", parent=_STYLES["Heading2"], fontSize=12, spaceAfter=6)
_NORMAL = _STYLES["Normal"]


def _header_table(title: str, reference: str, date_str: str) -> Table:
    """Company header + document title."""
    data = [
        [Paragraph("<b>LabSynch Equipment Services</b>", _NORMAL), "", ""],
        [Paragraph(title, _TITLE), "", ""],
        [f"Reference: {reference}", "", f"Date: {date_str}"],
    ]
    t = Table(data, colWidths=[8 * cm, 5 * cm, 5 * cm])
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (2, 0)),
        ("SPAN", (0, 1), (2, 1)),
        ("ALIGN", (0, 2), (0, 2), "LEFT"),
        ("ALIGN", (2, 2), (2, 2), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


# ---------------------------------------------------------------------------
# Payment Receipt PDF
# ---------------------------------------------------------------------------

def generate_receipt_pdf(payment) -> io.BytesIO:
    """Generate a payment receipt PDF and return it as an in-memory buffer."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    elements = []
    booking = payment.booking
    school = booking.school_profile

    # Header
    date_str = (payment.completed_at or payment.initiated_at).strftime("%d %b %Y, %H:%M")
    elements.append(_header_table("PAYMENT RECEIPT", payment.transaction_ref, date_str))
    elements.append(Spacer(1, 12))

    # School info
    elements.append(Paragraph("Billed To", _HEADING))
    school_info = f"""
    {school.school_name}<br/>
    {school.physical_address or 'N/A'}<br/>
    {school.county or 'N/A'}<br/>
    Contact: {school.contact_person or 'N/A'}
    """
    elements.append(Paragraph(school_info.strip(), _NORMAL))
    elements.append(Spacer(1, 10))

    # Payment details
    elements.append(Paragraph("Payment Details", _HEADING))
    pay_data = [
        ["Booking Reference", booking.booking_reference],
        ["Payment Method", payment.get_payment_method_display()],
        ["M-Pesa Transaction", payment.mpesa_transaction_id or "N/A"],
        ["Amount Paid (KES)", f"{payment.amount_paid:,.2f}"],
        ["Status", payment.get_payment_status_display()],
    ]
    pay_table = Table(pay_data, colWidths=[7 * cm, 11 * cm])
    pay_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.93, 0.93, 0.93)),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(pay_table)
    elements.append(Spacer(1, 10))

    # Booking line items
    elements.append(Paragraph("Booking Items", _HEADING))
    item_rows = [["#", "Equipment", "Qty", "Days", "Rate/Day", "Subtotal"]]
    for idx, item in enumerate(booking.booking_items.select_related("equipment").all(), start=1):
        days = (booking.return_date - booking.pickup_date).days or 1
        item_rows.append([
            str(idx),
            item.equipment.equipment_name,
            str(item.quantity),
            str(days),
            f"{item.unit_price:,.2f}",
            f"{item.subtotal:,.2f}",
        ])

    if booking.transport_cost:
        item_rows.append(["", "Transport Fee", "", "", "", f"{booking.transport_cost:,.2f}"])

    item_rows.append(["", "", "", "", "TOTAL (KES)", f"{booking.total_amount:,.2f}"])

    item_table = Table(item_rows, colWidths=[1.2 * cm, 6 * cm, 1.5 * cm, 1.5 * cm, 3 * cm, 3 * cm])
    item_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.7)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 20))

    # Footer
    elements.append(Paragraph("This is an electronically generated receipt.", _NORMAL))

    doc.build(elements)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Equipment Usage Contract PDF
# ---------------------------------------------------------------------------

def generate_contract_pdf(booking) -> io.BytesIO:
    """Generate an equipment usage agreement/contract PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    elements = []
    school = booking.school_profile

    date_str = booking.pickup_date.strftime("%d %b %Y")
    elements.append(_header_table("EQUIPMENT USAGE AGREEMENT", booking.booking_reference, date_str))
    elements.append(Spacer(1, 12))

    # Parties
    elements.append(Paragraph("Parties", _HEADING))
    parties = f"""
    <b>Lender:</b> LabSynch Equipment Services<br/>
    <b>Borrower:</b> {school.school_name}<br/>
    Registration No: {school.registration_number or 'N/A'}<br/>
    Address: {school.physical_address or 'N/A'}, {school.county or 'N/A'}<br/>
    Contact Person: {school.contact_person or 'N/A'}
    """
    elements.append(Paragraph(parties.strip(), _NORMAL))
    elements.append(Spacer(1, 10))

    # Terms
    elements.append(Paragraph("Agreement Terms", _HEADING))
    terms = f"""
    1. The Borrower agrees to collect/receive the equipment on <b>{booking.pickup_date.strftime('%d %b %Y')}</b>
       and return all items on or before <b>{booking.return_date.strftime('%d %b %Y')}</b>.<br/><br/>
    2. The Borrower shall use the equipment solely for educational purposes within
       the registered school premises.<br/><br/>
    3. The Borrower is responsible for the care and safe keeping of all equipment
       during the rental period.  Any loss, theft, or damage must be reported
       immediately.<br/><br/>
    4. In the event of damage or loss, the Borrower agrees to pay the assessed
       repair or replacement cost as determined by LabSynch.<br/><br/>
    5. Late returns will incur additional daily charges at the standard rental rate
       and may affect the Borrower's future booking ability.<br/><br/>
    6. LabSynch reserves the right to inspect equipment upon return and raise
       damage reports as necessary.<br/><br/>
    7. Either party may cancel the booking before dispatch, subject to applicable
       cancellation/refund policies.
    """
    elements.append(Paragraph(terms.strip(), _NORMAL))
    elements.append(Spacer(1, 10))

    # Equipment table
    elements.append(Paragraph("Equipment Covered", _HEADING))
    eq_rows = [["#", "Equipment", "Code", "Qty", "Rate/Day (KES)"]]
    for idx, item in enumerate(booking.booking_items.select_related("equipment").all(), start=1):
        eq_rows.append([
            str(idx),
            item.equipment.equipment_name,
            item.equipment.equipment_code,
            str(item.quantity),
            f"{item.unit_price:,.2f}",
        ])
    eq_table = Table(eq_rows, colWidths=[1.2 * cm, 6 * cm, 3 * cm, 2 * cm, 4 * cm])
    eq_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.7)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(eq_table)
    elements.append(Spacer(1, 10))

    # Financial summary
    elements.append(Paragraph("Financial Summary", _HEADING))
    fin_data = [
        ["Total Rental Amount (KES)", f"{booking.total_amount:,.2f}"],
    ]
    if booking.transport_cost:
        fin_data.append(["Transport Cost (incl.)", f"{booking.transport_cost:,.2f}"])

    fin_table = Table(fin_data, colWidths=[9 * cm, 7 * cm])
    fin_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(fin_table)
    elements.append(Spacer(1, 20))

    # Signature lines
    sig = """
    <br/><br/>
    ________________________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;________________________________<br/>
    <b>LabSynch Representative</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Borrower / School Representative</b><br/><br/>
    Date: ________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Date: ________________
    """
    elements.append(Paragraph(sig.strip(), _NORMAL))

    doc.build(elements)
    buf.seek(0)
    return buf
