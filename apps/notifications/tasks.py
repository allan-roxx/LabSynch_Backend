"""
Celery tasks for async email notifications.

All tasks accept IDs (not model instances) to remain idempotent and
safe to execute inside or outside an active transaction.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="notifications.send_booking_confirmation", bind=True, max_retries=3)
def send_booking_confirmation(self, booking_id: str):
    """Email the school user when a new booking is created."""
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.select_related(
            "school_profile__user"
        ).prefetch_related(
            "booking_items__equipment"
        ).get(id=booking_id)

        user = booking.school_profile.user
        items_summary = "\n".join(
            f"  - {item.equipment.equipment_name} x{item.quantity} "
            f"@ KES {item.unit_price}/day = KES {item.subtotal}"
            for item in booking.booking_items.all()
        )

        send_mail(
            subject=f"LabSynch — Booking Received ({booking.booking_reference})",
            message=(
                f"Hello {user.full_name},\n\n"
                f"Your booking {booking.booking_reference} has been received.\n\n"
                f"Rental Period: {booking.pickup_date} to {booking.return_date}\n\n"
                f"Equipment:\n{items_summary}\n\n"
                f"Total: KES {booking.total_amount}\n\n"
                f"Please complete payment via M-Pesa to confirm your booking.\n\n"
                f"\u2014 The LabSynch Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        logger.info(
            "Booking confirmation sent for %s to %s",
            booking.booking_reference, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to send booking confirmation for %s: %s",
            booking_id, str(exc), exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="notifications.send_payment_receipt", bind=True, max_retries=3)
def send_payment_receipt(self, payment_id: str):
    """Email the school user after a successful M-Pesa payment."""
    from apps.payments.models import Payment

    try:
        payment = Payment.objects.select_related(
            "booking__school_profile__user"
        ).get(id=payment_id)

        user = payment.booking.school_profile.user
        booking = payment.booking

        send_mail(
            subject=f"LabSynch — Payment Confirmed ({payment.transaction_ref})",
            message=(
                f"Hello {user.full_name},\n\n"
                f"Your payment for booking {booking.booking_reference} has been confirmed.\n\n"
                f"Payment Details:\n"
                f"  Reference : {payment.transaction_ref}\n"
                f"  Amount    : KES {payment.amount_paid}\n"
                f"  M-Pesa Code: {payment.mpesa_transaction_id or 'N/A'}\n"
                f"  Paid At   : {payment.completed_at}\n\n"
                f"Our team will contact you to arrange equipment pickup.\n\n"
                f"\u2014 The LabSynch Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        logger.info(
            "Payment receipt sent for %s to %s",
            payment.transaction_ref, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to send payment receipt for %s: %s",
            payment_id, str(exc), exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="notifications.send_equipment_issued_notification", bind=True, max_retries=3)
def send_equipment_issued_notification(self, issuance_id: str):
    """Notify the school user when physical equipment handover is recorded."""
    from apps.issuances.models import EquipmentIssuance

    try:
        issuance = EquipmentIssuance.objects.select_related(
            "booking__school_profile__user"
        ).get(id=issuance_id)

        user = issuance.booking.school_profile.user
        booking = issuance.booking

        send_mail(
            subject=f"LabSynch — Equipment Issued ({booking.booking_reference})",
            message=(
                f"Hello {user.full_name},\n\n"
                f"Your equipment for booking {booking.booking_reference} has been issued.\n\n"
                f"Please return all equipment in good condition by {booking.return_date}.\n"
                f"Failure to return on time will result in overdue charges.\n\n"
                f"\u2014 The LabSynch Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        logger.info(
            "Equipment issued notification sent for %s to %s",
            booking.booking_reference, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to send equipment issued notification for %s: %s",
            issuance_id, str(exc), exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="notifications.send_overdue_alerts")
def send_overdue_alerts():
    """
    Periodic task: transitions ISSUED bookings past their return_date to OVERDUE
    and emails the affected school.
    Scheduled via CELERY_BEAT_SCHEDULE (runs daily at 08:00 Africa/Nairobi).
    """
    from apps.bookings.models import Booking, BookingStatus

    today = timezone.now().date()
    overdue_qs = Booking.objects.filter(
        status=BookingStatus.ISSUED,
        return_date__lt=today,
    ).select_related("school_profile__user")

    count = 0
    for booking in overdue_qs:
        booking.status = BookingStatus.OVERDUE
        booking.save(update_fields=["status", "updated_at"])

        user = booking.school_profile.user
        try:
            send_mail(
                subject=f"LabSynch — OVERDUE Return: {booking.booking_reference}",
                message=(
                    f"Hello {user.full_name},\n\n"
                    f"Your equipment rental for booking {booking.booking_reference} is now OVERDUE.\n\n"
                    f"  Return date was : {booking.return_date}\n"
                    f"  Today           : {today}\n\n"
                    f"Please return the equipment immediately to avoid further charges.\n\n"
                    f"\u2014 The LabSynch Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except Exception as exc:
            logger.error(
                "Failed to send overdue alert for booking %s: %s",
                booking.booking_reference, str(exc),
            )
        count += 1

    logger.info("Overdue alert task: %d booking(s) marked overdue.", count)
    return count
