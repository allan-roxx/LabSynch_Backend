"""
Reporting services — aggregate queries across bookings, payments, equipment,
damages, and schools.  All functions return plain dicts suitable for
serialization.  No models are created in this app.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone

from apps.bookings.models import Booking, BookingItem, BookingStatus
from apps.damages.models import DamageReport, ResolutionStatus
from apps.equipment.models import Equipment, EquipmentCategory
from apps.payments.models import Payment
from apps.users.models import SchoolProfile

logger = logging.getLogger(__name__)



# Dashboard / KPI metrics


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

    today = now.date()
    today_pickups = Booking.objects.filter(pickup_date=today).count()
    today_returns = Booking.objects.filter(return_date=today).count()
    today_pending_payment = Booking.objects.filter(
        status=BookingStatus.PENDING,
        pickup_date=today,
    ).count()

    # -- 30-day daily trend: bookings created & revenue earned ----------
    thirty_days_ago = (now - timedelta(days=29)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    bookings_trend = [
        {"date": row["day"].strftime("%Y-%m-%d"), "count": row["count"]}
        for row in (
            Booking.objects.filter(created_at__gte=thirty_days_ago)
            .annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
    ]
    revenue_trend = [
        {"date": row["day"].strftime("%Y-%m-%d"), "revenue": str(row["revenue"])}
        for row in (
            Payment.objects.filter(
                payment_status="SUCCESS", completed_at__gte=thirty_days_ago
            )
            .annotate(day=TruncDay("completed_at"))
            .values("day")
            .annotate(revenue=Sum("amount_paid"))
            .order_by("day")
        )
    ]

    # -- Monthly bookings for last 12 months ----------------------------
    twelve_months_ago = (now - timedelta(days=365)).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    monthly_bookings = [
        {"month": row["month"].strftime("%Y-%m"), "count": row["count"]}
        for row in (
            Booking.objects.filter(created_at__gte=twelve_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
    ]
    monthly_revenue = [
        {"month": row["month"].strftime("%Y-%m"), "revenue": str(row["revenue"])}
        for row in (
            Payment.objects.filter(
                payment_status="SUCCESS", completed_at__gte=twelve_months_ago
            )
            .annotate(month=TruncMonth("completed_at"))
            .values("month")
            .annotate(revenue=Sum("amount_paid"))
            .order_by("month")
        )
    ]

    return {
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "overdue_bookings": overdue_bookings,
        "revenue_total": str(revenue_total),
        "revenue_this_month": str(revenue_this_month),
        "total_schools": total_schools,
        "total_equipment": total_equipment,
        "pending_damage_reports": pending_damage_reports,
        "today_pickups": today_pickups,
        "today_returns": today_returns,
        "today_pending_payment": today_pending_payment,
        "bookings_trend": bookings_trend,
        "revenue_trend": revenue_trend,
        "monthly_bookings": monthly_bookings,
        "monthly_revenue": monthly_revenue,
    }



# Booking analytics


_TRUNC_MAP = {"day": TruncDay, "week": TruncWeek, "month": TruncMonth}
_DATE_FMT = {"day": "%Y-%m-%d", "week": "%G-W%V", "month": "%Y-%m"}


def get_booking_report(
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str = "month",
) -> dict:
    """Booking counts grouped by status and by configurable time period."""
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

    trunc_fn = _TRUNC_MAP.get(granularity, TruncMonth)
    fmt = _DATE_FMT.get(granularity, "%Y-%m")
    by_period = [
        {"period": row["period"].strftime(fmt), "count": row["count"]}
        for row in (
            qs.annotate(period=trunc_fn("created_at"))
            .values("period")
            .annotate(count=Count("id"))
            .order_by("period")
        )
    ]

    return {
        "total": total,
        "by_status": by_status,
        "average_duration_days": avg_duration.days if avg_duration else None,
        "by_period": by_period,
    }



# Financial / revenue report


def get_financial_report(
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str = "month",
) -> dict:
    """Revenue breakdown: total, by configurable period, outstanding damages."""
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

    trunc_fn = _TRUNC_MAP.get(granularity, TruncMonth)
    fmt = _DATE_FMT.get(granularity, "%Y-%m")
    by_period = [
        {
            "period": row["period"].strftime(fmt),
            "revenue": str(row["revenue"]),
            "payment_count": row["payment_count"],
        }
        for row in (
            payments.annotate(period=trunc_fn("completed_at"))
            .values("period")
            .annotate(revenue=Sum("amount_paid"), payment_count=Count("id"))
            .order_by("period")
        )
    ]

    return {
        "total_revenue": str(total_revenue),
        "payment_count": payment_count,
        "outstanding_damage_cost": str(total_repair - total_paid),
        "by_period": by_period,
    }



# Equipment utilisation report


def get_equipment_report() -> list[dict]:
    """Per-equipment utilisation stats: times booked, revenue generated."""
    items = (
        BookingItem.objects.values(
            "equipment__id",
            "equipment__equipment_name",
            "equipment__equipment_code",
        )
        .annotate(
            times_booked=Count("id"),
            total_quantity_booked=Sum("quantity"),
            total_revenue=Sum("subtotal"),
        )
        .order_by("-times_booked")
    )
    return [
        {
            "equipment_id": row["equipment__id"],
            "equipment_name": row["equipment__equipment_name"],
            "equipment_code": row["equipment__equipment_code"],
            "times_booked": row["times_booked"],
            "total_quantity_booked": row["total_quantity_booked"],
            "total_revenue": row["total_revenue"],
        }
        for row in items
    ]



# Client activity report


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



# Profitability / P&L report


def get_profitability_report(
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str = "month",
) -> dict:
    """
    Full P&L for the leasing business:
      - Revenue broken down by source (rental, personnel, transport, penalties, damage recovery)
      - Cost breakdown (repair costs incurred vs amount recovered from schools)
      - Net profit and margin
      - Fleet book value
      - Per-period profitability time-series for charting
      - Equipment ROI (revenue generated vs acquisition cost, top 20)
    """
    # ------------------------------------------------------------------
    # Successful payments in the requested date range
    # ------------------------------------------------------------------
    payments = Payment.objects.filter(payment_status="SUCCESS")
    if start_date:
        payments = payments.filter(completed_at__date__gte=start_date)
    if end_date:
        payments = payments.filter(completed_at__date__lte=end_date)

    total_payments = payments.aggregate(total=Sum("amount_paid"))["total"] or Decimal("0.00")

    # ------------------------------------------------------------------
    # Revenue components from the bookings behind those payments
    # ------------------------------------------------------------------
    paid_booking_ids = payments.values("booking_id")          # subquery — no Python list
    paid_bookings_qs = Booking.objects.filter(id__in=paid_booking_ids)
    paid_items_qs = BookingItem.objects.filter(booking__in=paid_bookings_qs)

    item_agg = paid_items_qs.aggregate(
        rental=Sum("subtotal"),
        personnel=Sum("personnel_cost"),
    )
    rental_revenue = item_agg["rental"] or Decimal("0.00")
    personnel_revenue = item_agg["personnel"] or Decimal("0.00")

    booking_agg = paid_bookings_qs.aggregate(
        transport=Sum("transport_cost"),
        penalties_carried=Sum("penalty_carried_forward"),
    )
    transport_revenue = booking_agg["transport"] or Decimal("0.00")
    # Penalties collected = prior-booking penalties rolled into this payment
    # + this booking's own overdue penalty when it has been cleared/settled
    penalties_collected = booking_agg["penalties_carried"] or Decimal("0.00")
    penalties_collected += (
        paid_bookings_qs.filter(penalty_cleared=True)
        .aggregate(total=Sum("overdue_penalty"))["total"] or Decimal("0.00")
    )

    # ------------------------------------------------------------------
    # Damage reports in the date range (repair costs & school recoveries)
    # ------------------------------------------------------------------
    damage_qs = DamageReport.objects.all()
    if start_date:
        damage_qs = damage_qs.filter(created_at__date__gte=start_date)
    if end_date:
        damage_qs = damage_qs.filter(created_at__date__lte=end_date)

    damage_agg = damage_qs.aggregate(
        repair_assessed=Sum("repair_cost"),
        repair_recovered=Sum("amount_paid"),
    )
    repair_assessed = damage_agg["repair_assessed"] or Decimal("0.00")
    repair_recovered = damage_agg["repair_recovered"] or Decimal("0.00")
    net_repair_cost = max(repair_assessed - repair_recovered, Decimal("0.00"))

    # Current outstanding liability across ALL time (not date-filtered)
    all_outstanding = DamageReport.objects.filter(
        resolution_status__in=[ResolutionStatus.PENDING, ResolutionStatus.CHARGED],
    ).aggregate(
        total_repair=Sum("repair_cost"),
        total_paid=Sum("amount_paid"),
    )
    outstanding_gap = max(
        (all_outstanding["total_repair"] or Decimal("0.00"))
        - (all_outstanding["total_paid"] or Decimal("0.00")),
        Decimal("0.00"),
    )

    # ------------------------------------------------------------------
    # Fleet book value (capital snapshot — not date-filtered)
    # ------------------------------------------------------------------
    fleet_agg = Equipment.objects.filter(
        is_active=True, acquisition_cost__isnull=False
    ).aggregate(
        fleet_value=Sum("acquisition_cost"),
        fleet_count=Count("id"),
    )
    fleet_value = fleet_agg["fleet_value"] or Decimal("0.00")
    fleet_count = fleet_agg["fleet_count"] or 0

    # ------------------------------------------------------------------
    # Profitability summary
    # ------------------------------------------------------------------
    # gross_revenue = all cash in (booking payments + damage cash recovered)
    # total_costs   = all assessed repair costs paid/owed by LabSynch
    gross_revenue = total_payments + repair_recovered
    total_costs = repair_assessed
    net_profit = gross_revenue - total_costs
    margin_pct = (
        (net_profit / gross_revenue * 100).quantize(Decimal("0.01"))
        if gross_revenue
        else Decimal("0.00")
    )

    # ------------------------------------------------------------------
    # Per-period P&L trend (revenue, costs, net profit)
    # ------------------------------------------------------------------
    trunc_fn = _TRUNC_MAP.get(granularity, TruncMonth)
    fmt = _DATE_FMT.get(granularity, "%Y-%m")

    rev_by_period = {
        row["period"].strftime(fmt): row["revenue"]
        for row in (
            payments.annotate(period=trunc_fn("completed_at"))
            .values("period")
            .annotate(revenue=Sum("amount_paid"))
            .order_by("period")
        )
    }
    cost_by_period = {
        row["period"].strftime(fmt): row["costs"]
        for row in (
            damage_qs.filter(repair_cost__isnull=False)
            .annotate(period=trunc_fn("created_at"))
            .values("period")
            .annotate(costs=Sum("repair_cost"))
            .order_by("period")
        )
    }
    recovery_by_period = {
        row["period"].strftime(fmt): row["recovered"]
        for row in (
            damage_qs.filter(amount_paid__gt=0)
            .annotate(period=trunc_fn("created_at"))
            .values("period")
            .annotate(recovered=Sum("amount_paid"))
            .order_by("period")
        )
    }

    all_periods = sorted(set(rev_by_period) | set(cost_by_period) | set(recovery_by_period))
    profitability_trend = []
    for p in all_periods:
        rev = rev_by_period.get(p) or Decimal("0.00")
        cost = cost_by_period.get(p) or Decimal("0.00")
        recovered = recovery_by_period.get(p) or Decimal("0.00")
        gross = rev + recovered
        net = gross - cost
        profitability_trend.append({
            "period": p,
            "gross_revenue": str(gross),
            "repair_costs": str(cost),
            "damage_recovery": str(recovered),
            "net_profit": str(net),
        })

    # ------------------------------------------------------------------
    # Equipment ROI — top 20 earners where acquisition cost is recorded
    # ------------------------------------------------------------------
    roi_rows = (
        BookingItem.objects.filter(
            equipment__acquisition_cost__isnull=False,
            equipment__is_active=True,
        )
        .values(
            "equipment__id",
            "equipment__equipment_name",
            "equipment__acquisition_cost",
        )
        .annotate(total_revenue_generated=Sum("subtotal"))
        .order_by("-total_revenue_generated")[:20]
    )
    equipment_roi = []
    for row in roi_rows:
        acq = row["equipment__acquisition_cost"] or Decimal("0.00")
        rev_gen = row["total_revenue_generated"] or Decimal("0.00")
        roi_val = (
            ((rev_gen - acq) / acq * 100).quantize(Decimal("0.01"))
            if acq
            else None
        )
        equipment_roi.append({
            "equipment_id": str(row["equipment__id"]),
            "equipment_name": row["equipment__equipment_name"],
            "acquisition_cost": str(acq),
            "total_revenue_generated": str(rev_gen),
            "roi_pct": str(roi_val) if roi_val is not None else None,
        })

    return {
        "summary": {
            "total_payments_received": str(total_payments),
            "damage_recovery": str(repair_recovered),
            "gross_revenue": str(gross_revenue),
            "total_repair_costs": str(total_costs),
            "net_profit": str(net_profit),
            "profit_margin_pct": str(margin_pct),
        },
        "revenue_breakdown": {
            "rental": str(rental_revenue),
            "personnel": str(personnel_revenue),
            "transport": str(transport_revenue),
            "penalties": str(penalties_collected),
            "damage_recovery": str(repair_recovered),
        },
        "damage_analysis": {
            "total_repair_cost_assessed": str(repair_assessed),
            "total_recovered_from_schools": str(repair_recovered),
            "net_unrecovered_repair_cost": str(net_repair_cost),
            "all_time_outstanding_liability": str(outstanding_gap),
        },
        "fleet_overview": {
            "total_active_equipment": fleet_count,
            "total_fleet_acquisition_value": str(fleet_value),
        },
        "profitability_trend": profitability_trend,
        "equipment_roi": equipment_roi,
    }
