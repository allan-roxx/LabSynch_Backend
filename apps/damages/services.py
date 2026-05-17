"""
Services for Damage Reports.
"""

import logging
from datetime import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import BookingItem
from apps.issuances.models import EquipmentReturn
from apps.payments.services import generate_mpesa_password, get_mpesa_access_token
from apps.users.models import LiabilityStatus
from rest_framework.exceptions import ValidationError
from .models import DamagePaymentStatus, DamageReport, DamageSettlementPayment, ResolutionStatus
from apps.audit.services import log_action
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


def generate_damage_transaction_reference() -> str:
    year = timezone.now().year
    count = DamageSettlementPayment.objects.filter(initiated_at__year=year).count() + 1
    return f"DMG-TXN-{year}-{count:04d}"


def _get_damage_callback_url() -> str:
    explicit = getattr(settings, "MPESA_DAMAGE_CALLBACK_URL", "")
    if explicit:
        return explicit

    booking_callback = getattr(settings, "MPESA_CALLBACK_URL", "")
    if booking_callback and "/payments/mpesa-callback/" in booking_callback:
        return booking_callback.replace("/payments/mpesa-callback/", "/damages/mpesa-callback/")

    return "http://localhost:8000/api/damages/mpesa-callback/"


def _update_school_liability(school_profile):
    """
    Recalculate the school's liability_status based on outstanding damage reports.
    """
    has_outstanding = DamageReport.objects.filter(
        equipment_return__booking__school_profile=school_profile,
        resolution_status__in=[ResolutionStatus.PENDING, ResolutionStatus.CHARGED],
    ).exists()

    new_status = LiabilityStatus.HAS_OUTSTANDING if has_outstanding else LiabilityStatus.CLEAR
    if school_profile.liability_status != new_status:
        school_profile.liability_status = new_status
        school_profile.save(update_fields=["liability_status", "updated_at"])
        logger.info(
            "School %s liability_status updated to %s",
            school_profile.id, new_status,
        )


@transaction.atomic
def create_damage_report(
    equipment_return: EquipmentReturn,
    booking_item: BookingItem,
    reported_by,
    quantity_damaged: int,
    severity: str,
    description: str,
    photo_urls: list = None,
    repair_cost=None,
) -> DamageReport:
    """
    Creates a formal damage report linking an executed return to a specific line item.
    Sets the school's liability_status to HAS_OUTSTANDING.
    """
    if booking_item.booking != equipment_return.booking:
        raise ValidationError({"booking_item": "This item does not belong to the returned booking."})
        
    if quantity_damaged > booking_item.quantity:
        raise ValidationError({"quantity_damaged": "Cannot report more damaged items than were initially booked."})
        
    report = DamageReport.objects.create(
        equipment_return=equipment_return,
        booking_item=booking_item,
        reported_by=reported_by,
        quantity_damaged=quantity_damaged,
        severity=severity,
        description=description,
        photo_urls=photo_urls or [],
        repair_cost=repair_cost,
    )

    log_action(
        action=AuditLog.Action.CREATE,
        instance=report,
        actor=reported_by,
        changes={"severity": severity, "quantity_damaged": quantity_damaged},
    )

    # Update school liability
    school_profile = equipment_return.booking.school_profile
    _update_school_liability(school_profile)

    return report


@transaction.atomic
def resolve_damage_report(
    damage_report: DamageReport,
    resolution_status: str,
    repair_cost=None,
    amount_paid=None,
) -> DamageReport:
    """
    Updates the damage report resolution (e.g. charging the school or waiving).
    Recalculates school liability after resolution.
    """
    if resolution_status not in [choice[0] for choice in ResolutionStatus.choices]:
        raise ValidationError({"resolution_status": "Invalid resolution status."})
        
    damage_report.resolution_status = resolution_status
    update_fields = ["resolution_status", "updated_at"]

    if repair_cost is not None:
        damage_report.repair_cost = repair_cost
        update_fields.append("repair_cost")
    if amount_paid is not None:
        damage_report.amount_paid = amount_paid
        update_fields.append("amount_paid")

    damage_report.save(update_fields=update_fields)

    log_action(
        action=AuditLog.Action.RESOLVE,
        instance=damage_report,
        changes={
            "resolution_status": resolution_status,
            "repair_cost": str(repair_cost) if repair_cost else None,
        },
    )

    # Recalculate school liability
    school_profile = damage_report.equipment_return.booking.school_profile
    _update_school_liability(school_profile)

    return damage_report


@transaction.atomic
def settle_damage_report_by_school(
    damage_report: DamageReport,
    school_user,
    phone_number: str,
) -> DamageSettlementPayment:
    """
    Initiate an M-Pesa STK push to settle damage liability.
    Actual resolution status update happens on callback success.
    """
    if damage_report.equipment_return.booking.school_profile.user_id != school_user.id:
        raise ValidationError({"detail": "You can only settle liabilities for your own school."})

    if damage_report.resolution_status in [ResolutionStatus.WAIVED, ResolutionStatus.RESOLVED]:
        raise ValidationError({"resolution_status": "This damage report is already closed."})

    if damage_report.repair_cost is None or damage_report.repair_cost <= 0:
        raise ValidationError({"repair_cost": "Liability cannot be settled before repair cost assessment."})

    outstanding = Decimal(str(damage_report.amount_outstanding or 0)).quantize(Decimal("0.01"))
    if outstanding <= 0:
        raise ValidationError({"amount_paid": "This liability is already fully settled."})

    if phone_number.startswith("0"):
        phone_number = f"254{phone_number[1:]}"
    elif phone_number.startswith("+"):
        phone_number = phone_number[1:]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = generate_mpesa_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY, timestamp)
    callback_url = _get_damage_callback_url()
    amount = max(1, int(outstanding))

    settlement = DamageSettlementPayment.objects.create(
        transaction_ref=generate_damage_transaction_reference(),
        damage_report=damage_report,
        amount_paid=Decimal(str(amount)),
        mpesa_phone_number=phone_number,
        payment_status=DamagePaymentStatus.PENDING,
    )

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": damage_report.equipment_return.booking.booking_reference,
        "TransactionDesc": f"Damage settlement {damage_report.id}",
    }

    access_token = get_mpesa_access_token()
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    if access_token != "dummy_token":
        url = f"{settings.MPESA_ENVIRONMENT_URL}/mpesa/stkpush/v1/processrequest"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            settlement.mpesa_checkout_request_id = data.get("CheckoutRequestID")
            settlement.save(update_fields=["mpesa_checkout_request_id", "updated_at"])
        except requests.exceptions.HTTPError as exc:
            settlement.payment_status = DamagePaymentStatus.FAILED
            settlement.save(update_fields=["payment_status", "updated_at"])
            raise ValidationError({"mpesa": "Failed to initiate M-Pesa prompt. Please try again."}) from exc
        except requests.exceptions.RequestException as exc:
            settlement.payment_status = DamagePaymentStatus.FAILED
            settlement.save(update_fields=["payment_status", "updated_at"])
            raise ValidationError({"mpesa": "Failed to initiate M-Pesa prompt. Please try again."}) from exc
    else:
        settlement.mpesa_checkout_request_id = f"ws_CO_DMG_{timestamp}_mock"
        settlement.save(update_fields=["mpesa_checkout_request_id", "updated_at"])

    return settlement


@transaction.atomic
def process_damage_settlement_callback(payload: dict) -> None:
    """Process Daraja callback for damage settlement STK requests."""
    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")

    if not checkout_request_id:
        logger.warning("Damage callback missing CheckoutRequestID")
        return

    try:
        settlement = DamageSettlementPayment.objects.select_for_update().select_related(
            "damage_report", "damage_report__equipment_return__booking__school_profile"
        ).get(mpesa_checkout_request_id=checkout_request_id)
    except DamageSettlementPayment.DoesNotExist:
        logger.warning("Damage settlement with CheckoutRequestID %s not found", checkout_request_id)
        return

    if settlement.payment_status != DamagePaymentStatus.PENDING:
        return

    settlement.callback_response = payload
    settlement.completed_at = timezone.now()

    if result_code == 0:
        callback_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        for item in callback_items:
            if item.get("Name") == "MpesaReceiptNumber":
                settlement.mpesa_transaction_id = str(item.get("Value"))

        settlement.payment_status = DamagePaymentStatus.SUCCESS
        settlement.save(
            update_fields=[
                "payment_status", "mpesa_transaction_id", "completed_at", "callback_response", "updated_at"
            ]
        )

        report = settlement.damage_report
        current_paid = Decimal(str(report.amount_paid or 0))
        repair_cost = Decimal(str(report.repair_cost or 0))
        new_paid = current_paid + Decimal(str(settlement.amount_paid))

        if new_paid >= repair_cost:
            report.amount_paid = repair_cost
            report.resolution_status = ResolutionStatus.PAID
        else:
            report.amount_paid = new_paid
            report.resolution_status = ResolutionStatus.CHARGED

        report.save(update_fields=["amount_paid", "resolution_status", "updated_at"])

        log_action(
            action=AuditLog.Action.PAYMENT,
            instance=report,
            actor=report.equipment_return.booking.school_profile.user,
            changes={
                "amount_paid": str(settlement.amount_paid),
                "resolution_status": report.resolution_status,
                "transaction_ref": settlement.transaction_ref,
            },
        )

        _update_school_liability(report.equipment_return.booking.school_profile)
    else:
        settlement.payment_status = DamagePaymentStatus.FAILED
        settlement.save(update_fields=["payment_status", "completed_at", "callback_response", "updated_at"])
