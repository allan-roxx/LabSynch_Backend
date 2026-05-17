"""
Celery tasks for async email notifications.

All tasks accept IDs (not model instances) to remain idempotent and
safe to execute inside or outside an active transaction.
Each task also creates an in-app Notification record via services.py.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import NotificationType
from .services import create_notification

logger = logging.getLogger(__name__)


def _send_email_or_log(*, subject: str, message: str, recipient_list: list[str]) -> None:
    """Best-effort email delivery; disabled by default when no email service is configured."""
    if not getattr(settings, "ENABLE_NOTIFICATION_EMAILS", False):
        logger.info("Notification emails disabled; skipping email for %s", recipient_list)
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
        )
    except Exception as exc:
        logger.warning("Email send skipped/failed for %s: %s", recipient_list, str(exc))


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

        body = (
            f"Your booking {booking.booking_reference} has been received.\n\n"
            f"Rental Period: {booking.pickup_date} to {booking.return_date}\n\n"
            f"Equipment:\n{items_summary}\n\n"
            f"Total: KES {booking.total_amount}\n\n"
            f"Please complete payment via M-Pesa to confirm your booking."
        )

        create_notification(
            user=user,
            notification_type=NotificationType.BOOKING_CREATED,
            title=f"Booking {booking.booking_reference} received",
            body=body,
            booking_id=booking.id,
        )

        _send_email_or_log(
            subject=f"LabSynch — Booking Received ({booking.booking_reference})",
            message=f"Hello {user.full_name},\n\n{body}\n\n— The LabSynch Team",
            recipient_list=[user.email],
        )

        logger.info(
            "Booking confirmation sent for %s to %s",
            booking.booking_reference, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to process booking confirmation for %s: %s",
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

        body = (
            f"Your payment for booking {booking.booking_reference} has been confirmed.\n\n"
            f"Payment Details:\n"
            f"  Reference  : {payment.transaction_ref}\n"
            f"  Amount     : KES {payment.amount_paid}\n"
            f"  M-Pesa Code: {payment.mpesa_transaction_id or 'N/A'}\n"
            f"  Paid At    : {payment.completed_at}\n\n"
            f"Our team will contact you to arrange equipment pickup."
        )

        create_notification(
            user=user,
            notification_type=NotificationType.PAYMENT_RECEIVED,
            title=f"Payment confirmed for {booking.booking_reference}",
            body=body,
            booking_id=booking.id,
            payment_id=payment.id,
        )

        _send_email_or_log(
            subject=f"LabSynch — Payment Confirmed ({payment.transaction_ref})",
            message=f"Hello {user.full_name},\n\n{body}\n\n— The LabSynch Team",
            recipient_list=[user.email],
        )

        logger.info(
            "Payment receipt sent for %s to %s",
            payment.transaction_ref, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to process payment receipt for %s: %s",
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

        body = (
            f"Your equipment for booking {booking.booking_reference} has been issued.\n\n"
            f"Please return all equipment in good condition by {booking.return_date}.\n"
            f"Failure to return on time will result in overdue charges."
        )

        create_notification(
            user=user,
            notification_type=NotificationType.EQUIPMENT_ISSUED,
            title=f"Equipment issued for {booking.booking_reference}",
            body=body,
            booking_id=booking.id,
            issuance_id=issuance.id,
        )

        _send_email_or_log(
            subject=f"LabSynch — Equipment Issued ({booking.booking_reference})",
            message=f"Hello {user.full_name},\n\n{body}\n\n— The LabSynch Team",
            recipient_list=[user.email],
        )

        logger.info(
            "Equipment issued notification sent for %s to %s",
            booking.booking_reference, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to process equipment issued notification for %s: %s",
            issuance_id, str(exc), exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="notifications.send_overdue_alerts")
def send_overdue_alerts():
    """
    Periodic task: transitions IN_USE bookings past their return_date to OVERDUE
    and emails the affected school.
    Scheduled via CELERY_BEAT_SCHEDULE (runs daily at 08:00 Africa/Nairobi).
    """
    from apps.bookings.models import Booking, BookingStatus

    today = timezone.now().date()
    overdue_qs = Booking.objects.filter(
        status=BookingStatus.IN_USE,
        return_date__lt=today,
    ).select_related("school_profile__user")

    count = 0
    for booking in overdue_qs:
        booking.status = BookingStatus.OVERDUE
        booking.save(update_fields=["status", "updated_at"])

        user = booking.school_profile.user
        body = (
            f"Your equipment rental for booking {booking.booking_reference} is now OVERDUE.\n\n"
            f"  Return date was : {booking.return_date}\n"
            f"  Today           : {today}\n\n"
            f"Please return the equipment immediately to avoid further charges."
        )

        try:
            send_mail(
                subject=f"LabSynch — OVERDUE Return: {booking.booking_reference}",
                message=f"Hello {user.full_name},\n\n{body}\n\n— The LabSynch Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except Exception as exc:
            logger.error(
                "Failed to send overdue alert email for booking %s: %s",
                booking.booking_reference, str(exc),
            )

        create_notification(
            user=user,
            notification_type=NotificationType.EQUIPMENT_OVERDUE,
            title=f"Overdue: {booking.booking_reference}",
            body=body,
            booking_id=booking.id,
        )

        count += 1

    logger.info("Overdue alert task: %d booking(s) marked overdue.", count)
    return count


@shared_task(name="notifications.send_equipment_returned_notification", bind=True, max_retries=3)
def send_equipment_returned_notification(self, booking_id: str):
    """Notify the school user when their equipment return is recorded."""
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.select_related("school_profile__user").get(id=booking_id)
        user = booking.school_profile.user

        penalty_line = ""
        if booking.overdue_penalty and booking.overdue_penalty > 0:
            penalty_line = (
                f"\n\nNote: An overdue penalty of KES {booking.overdue_penalty} has been recorded. "
                f"This must be settled before your next booking."
            )

        body = (
            f"The equipment for booking {booking.booking_reference} has been returned successfully.\n\n"
            f"Return recorded on: {timezone.now().date()}"
            f"{penalty_line}"
        )

        create_notification(
            user=user,
            notification_type=NotificationType.EQUIPMENT_RETURNED,
            title=f"Equipment returned for {booking.booking_reference}",
            body=body,
            booking_id=booking.id,
        )

        _send_email_or_log(
            subject=f"LabSynch — Equipment Returned ({booking.booking_reference})",
            message=f"Hello {user.full_name},\n\n{body}\n\n— The LabSynch Team",
            recipient_list=[user.email],
        )

        logger.info(
            "Equipment returned notification sent for %s to %s",
            booking.booking_reference, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to process equipment returned notification for %s: %s",
            booking_id, str(exc), exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="notifications.send_booking_cancelled_notification", bind=True, max_retries=3)
def send_booking_cancelled_notification(self, booking_id: str):
    """Notify the school user when their booking is cancelled."""
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.select_related("school_profile__user").get(id=booking_id)
        user = booking.school_profile.user

        body = (
            f"Your booking {booking.booking_reference} has been cancelled.\n\n"
            f"If you did not request this cancellation, please contact support."
        )

        create_notification(
            user=user,
            notification_type=NotificationType.BOOKING_CANCELLED,
            title=f"Booking {booking.booking_reference} cancelled",
            body=body,
            booking_id=booking.id,
        )

        _send_email_or_log(
            subject=f"LabSynch — Booking Cancelled ({booking.booking_reference})",
            message=f"Hello {user.full_name},\n\n{body}\n\n— The LabSynch Team",
            recipient_list=[user.email],
        )

        logger.info(
            "Booking cancelled notification sent for %s to %s",
            booking.booking_reference, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to process booking cancelled notification for %s: %s",
            booking_id, str(exc), exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="notifications.send_penalty_cleared_notification", bind=True, max_retries=3)
def send_penalty_cleared_notification(self, booking_id: str):
    """Notify the school user when their overdue penalty is cleared by an admin."""
    from apps.bookings.models import Booking

    try:
        booking = Booking.objects.select_related("school_profile__user").get(id=booking_id)
        user = booking.school_profile.user

        body = (
            f"The overdue penalty of KES {booking.overdue_penalty} on booking "
            f"{booking.booking_reference} has been cleared by LabSynch staff.\n\n"
            f"You can now make new bookings."
        )

        create_notification(
            user=user,
            notification_type=NotificationType.PENALTY_CLEARED,
            title=f"Penalty cleared for {booking.booking_reference}",
            body=body,
            booking_id=booking.id,
        )

        _send_email_or_log(
            subject=f"LabSynch — Penalty Cleared ({booking.booking_reference})",
            message=f"Hello {user.full_name},\n\n{body}\n\n— The LabSynch Team",
            recipient_list=[user.email],
        )

        logger.info(
            "Penalty cleared notification sent for %s to %s",
            booking.booking_reference, user.email,
        )
    except Exception as exc:
        logger.error(
            "Failed to process penalty cleared notification for %s: %s",
            booking_id, str(exc), exc_info=True,
        )
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="notifications.check_at_risk_bookings")
def check_at_risk_bookings():
    """
    Periodic task: detects RESERVED bookings whose upcoming dispatch is threatened
    by OVERDUE equipment that has not been physically returned.

    Logic:
      1. Find all RESERVED bookings with pickup_date within the next 3 days.
      2. For each BookingItem, sum how many units of that equipment are held by
         OVERDUE bookings. If (overdue_held + needed) > total_quantity there is a
         physical shortfall at dispatch time.
      3. Notify the affected school AND all admin users.

    Scheduled daily at 08:05 Africa/Nairobi (just after send_overdue_alerts so
    OVERDUE statuses are already updated for the day).
    """
    from datetime import timedelta

    from django.db.models import Sum

    from apps.bookings.models import Booking, BookingItem, BookingStatus
    from apps.users.models import User, UserType

    today = timezone.now().date()
    horizon = today + timedelta(days=3)

    at_risk_bookings = (
        Booking.objects.filter(
            status=BookingStatus.RESERVED,
            pickup_date__gte=today,
            pickup_date__lte=horizon,
        )
        .select_related("school_profile__user")
        .prefetch_related("booking_items__equipment")
    )

    admins = list(User.objects.filter(user_type=UserType.ADMIN, is_active=True))

    count = 0
    for booking in at_risk_bookings:
        risk_items = []
        for item in booking.booking_items.all():
            equipment = item.equipment
            overdue_held = (
                BookingItem.objects.filter(
                    equipment=equipment,
                    booking__status=BookingStatus.OVERDUE,
                ).aggregate(total=Sum("quantity"))["total"] or 0
            )
            # Physical shortfall: overdue units + what this school needs > stock on hand
            if overdue_held + item.quantity > equipment.total_quantity:
                risk_items.append(
                    (equipment.equipment_name, item.quantity, overdue_held, equipment.total_quantity)
                )

        if not risk_items:
            continue

        items_str = "\n".join(
            f"  - {name}: you need {needed} unit(s), "
            f"but {overdue} of {total} are still OVERDUE"
            for name, needed, overdue, total in risk_items
        )
        school_body = (
            f"Your booking {booking.booking_reference} (pickup: {booking.pickup_date}) "
            f"may be affected because some equipment has not yet been returned by "
            f"another party.\n\n"
            f"Affected items:\n{items_str}\n\n"
            f"Our team is actively working to resolve this and will contact you if "
            f"there is any change to your booking. We sincerely apologise for any "
            f"inconvenience."
        )
        admin_body = (
            f"ACTION REQUIRED\n\n"
            f"Booking {booking.booking_reference} for "
            f"{booking.school_profile.school_name} (pickup: {booking.pickup_date}) "
            f"is AT RISK. The following equipment is still held by overdue bookings:\n\n"
            f"{items_str}\n\n"
            f"Please chase the return of the overdue equipment immediately."
        )

        user = booking.school_profile.user
        try:
            send_mail(
                subject=f"LabSynch \u2014 Your Booking {booking.booking_reference} May Be Affected",
                message=f"Hello {user.full_name},\n\n{school_body}\n\n\u2014 The LabSynch Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except Exception as exc:
            logger.error(
                "Failed to email school for at-risk booking %s: %s",
                booking.booking_reference, str(exc),
            )

        create_notification(
            user=user,
            notification_type=NotificationType.BOOKING_AT_RISK,
            title=f"Booking {booking.booking_reference} may be affected",
            body=school_body,
            booking_id=booking.id,
        )

        for admin in admins:
            try:
                send_mail(
                    subject=f"LabSynch \u2014 AT RISK: {booking.booking_reference}",
                    message=f"Hello {admin.full_name},\n\n{admin_body}\n\n\u2014 LabSynch System",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[admin.email],
                )
            except Exception as exc:
                logger.error(
                    "Failed to email admin %s for at-risk booking %s: %s",
                    admin.email, booking.booking_reference, str(exc),
                )

            create_notification(
                user=admin,
                notification_type=NotificationType.BOOKING_AT_RISK,
                title=f"AT RISK: {booking.booking_reference}",
                body=admin_body,
                booking_id=booking.id,
            )

        count += 1
        logger.info(
            "At-risk booking flagged: %s (pickup: %s)",
            booking.booking_reference, booking.pickup_date,
        )

    logger.info("At-risk booking check complete: %d booking(s) flagged.", count)
    return count
