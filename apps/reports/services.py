"""
Reporting services — aggregate queries across bookings, payments, equipment,
damages, and schools.  All functions return plain dicts suitable for
serialization.  No models are created in this app.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

from apps.bookings.models import Booking, BookingItem, BookingStatus
from apps.damages.models import DamageReport, ResolutionStatus
from apps.equipment.models import Equipment, EquipmentCategory
from apps.payments.models import Payment
from apps.users.models import SchoolProfile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dashboard / KPI metrics
# ---------------------------------------------------------------------------

def get_dashboard_metrics() -> dict:
    """Top-level KPIs for the admin dashboard."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_bookings = Booking.objects.count()
    active_bookings = Booking.objects.filter(
        status__in=[
            BookingStatus.RESERVED,
            BookingStatus.DISPATCHED,
            BookingStatus.IN_USE,
        ]
    ).count()
    overdue_bookings = Booking.objects.filter(status=BookingStatus.OVERDUE).count()

    revenue_total = Payment.objects.filter(
        payment_status="SUCCESS",
    ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")

    revenue_this_month = Payment.objects.filter(
        payment_status="SUCCESS",
        completed_at__gte=month_start,
    ).aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")

    total_schools = SchoolProfile.objects.count()
    total_equipment = Equipment.objects.filter(is_active=True).count()

    pending_damage_reports = DamageReport.objects.filter(
        resolution_status=ResolutionStatus.PENDING,
    ).count()

    return {
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "overdue_bookings": overdue_bookings,
        "revenue_total": str(revenue_total),
        "revenue_this_month": str(revenue_this_month),
        "total_schools": total_schools,
        "total_equipment": total_equipment,
        "pending_damage_reports": pending_damage_reports,
    }


# ---------------------------------------------------------------------------
# Booking analytics
# ---------------------------------------------------------------------------

def get_booking_report(start_date: date | None = None, end_date: date | None = None) -> dict:
    """Booking counts grouped by status and by month."""
    qs = Booking.objects.all()
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    by_status = dict(
        qs.values_list("status").annotate(count=Count("id")).values_list("status", "count")
    )

    total = qs.count()
    avg_duration = qs.filter(
        pickup_date__isnull=False, return_date__isnull=False,
    ).annotate(
        duration=F("return_date") - F("pickup_date"),
    ).aggregate(avg=Avg("duration"))["avg"]

    return {
        "total": total,
        "by_status": by_status,
        "average_duration_days": avg_duration.days if avg_duration else None,
    }


# ---------------------------------------------------------------------------
# Financial / revenue report
# ---------------------------------------------------------------------------

def get_financial_report(start_date: date | None = None, end_date: date | None = None) -> dict:
    """Revenue breakdown: total, by month, outstanding damages."""
    payments = Payment.objects.filter(payment_status="SUCCESS")
    if start_date:
        payments = payments.filter(completed_at__date__gte=start_date)
    if end_date:
        payments = payments.filter(completed_at__date__lte=end_date)

    total_revenue = payments.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")
    payment_count = payments.count()

    outstanding_damages = DamageReport.objects.filter(
        resolution_status__in=[ResolutionStatus.PENDING, ResolutionStatus.CHARGED],
    ).aggregate(
        total_repair_cost=Sum("repair_cost"),
        total_paid=Sum("amount_paid"),
    )
    total_repair = outstanding_damages["total_repair_cost"] or Decimal("0.00")
    total_paid = outstanding_damages["total_paid"] or Decimal("0.00")

    return {
        "total_revenue": str(total_revenue),
        "payment_count": payment_count,
        "outstanding_damage_cost": str(total_repair - total_paid),
    }


# ---------------------------------------------------------------------------
# Equipment utilisation report
# ---------------------------------------------------------------------------

def get_equipment_report() -> list[dict]:
    """Per-equipment utilisation stats: times booked, revenue generated."""
    items = (
        BookingItem.objects.values(
            equipment_id=F("equipment__id"),
            equipment_name=F("equipment__equipment_name"),
            equipment_code=F("equipment__equipment_code"),
        )
        .annotate(
            times_booked=Count("id"),
            total_quantity_booked=Sum("quantity"),
            total_revenue=Sum("subtotal"),
        )
        .order_by("-times_booked")
    )
    return list(items)


# ---------------------------------------------------------------------------
# Client activity report
# ---------------------------------------------------------------------------

def get_client_report() -> list[dict]:
    """Per-school: booking count, total spend, liability status."""
    schools = (
        SchoolProfile.objects
        .annotate(
            booking_count=Count("bookings"),
            total_spend=Sum("bookings__total_amount"),
        )
        .values(
            "id",
            "school_name",
            "county",
            "liability_status",
            "booking_count",
            "total_spend",
        )
        .order_by("-booking_count")
    )
    return list(schools)
