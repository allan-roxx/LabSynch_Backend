"""
Tests for the Notifications Celery tasks.
Tasks are called synchronously (no broker needed) in these unit tests.
send_mail is mocked to avoid hitting an SMTP server.
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from apps.bookings.models import BookingStatus
from apps.notifications.tasks import (
    send_booking_confirmation,
    send_equipment_issued_notification,
    send_overdue_alerts,
    send_payment_receipt,
)
from tests.factories import BookingFactory, PaymentFactory, SchoolProfileFactory


@pytest.mark.django_db
def test_send_booking_confirmation_sends_email():
    booking = BookingFactory()

    with patch("apps.notifications.tasks.send_mail") as mock_mail:
        send_booking_confirmation(str(booking.id))

    mock_mail.assert_called_once()
    _, kwargs = mock_mail.call_args
    assert booking.booking_reference in kwargs["subject"]
    assert booking.school_profile.user.email in kwargs["recipient_list"]


@pytest.mark.django_db
def test_send_payment_receipt_sends_email():
    payment = PaymentFactory()

    with patch("apps.notifications.tasks.send_mail") as mock_mail:
        send_payment_receipt(str(payment.id))

    mock_mail.assert_called_once()
    _, kwargs = mock_mail.call_args
    assert payment.transaction_ref in kwargs["subject"]
    assert payment.booking.school_profile.user.email in kwargs["recipient_list"]


@pytest.mark.django_db
def test_send_overdue_alerts_marks_issued_past_return_date():
    booking = BookingFactory(
        status=BookingStatus.ISSUED,
        pickup_date=date.today() - timedelta(days=10),
        return_date=date.today() - timedelta(days=2),
    )

    with patch("apps.notifications.tasks.send_mail"):
        count = send_overdue_alerts()

    assert count == 1
    booking.refresh_from_db()
    assert booking.status == BookingStatus.OVERDUE


@pytest.mark.django_db
def test_send_overdue_alerts_ignores_future_return_dates():
    booking = BookingFactory(
        status=BookingStatus.ISSUED,
        pickup_date=date.today() + timedelta(days=1),
        return_date=date.today() + timedelta(days=5),
    )

    with patch("apps.notifications.tasks.send_mail"):
        count = send_overdue_alerts()

    assert count == 0
    booking.refresh_from_db()
    assert booking.status == BookingStatus.ISSUED


@pytest.mark.django_db
def test_send_overdue_alerts_skips_non_issued_bookings():
    """PAID bookings past return_date should NOT be touched by the overdue task."""
    booking = BookingFactory(
        status=BookingStatus.PAID,
        pickup_date=date.today() - timedelta(days=10),
        return_date=date.today() - timedelta(days=2),
    )

    with patch("apps.notifications.tasks.send_mail"):
        count = send_overdue_alerts()

    assert count == 0
    booking.refresh_from_db()
    assert booking.status == BookingStatus.PAID


@pytest.mark.django_db
def test_send_overdue_alerts_returns_correct_count():
    with patch("apps.notifications.tasks.send_mail"):
        # Create 3 overdue + 1 future
        for _ in range(3):
            BookingFactory(
                status=BookingStatus.ISSUED,
                pickup_date=date.today() - timedelta(days=10),
                return_date=date.today() - timedelta(days=1),
            )
        BookingFactory(
            status=BookingStatus.ISSUED,
            pickup_date=date.today() + timedelta(days=1),
            return_date=date.today() + timedelta(days=5),
        )
        count = send_overdue_alerts()

    assert count == 3
