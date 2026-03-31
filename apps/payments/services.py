import base64
import logging
from datetime import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from rest_framework.exceptions import ValidationError
from .models import Payment, PaymentMethod, PaymentStatus

logger = logging.getLogger(__name__)


def generate_mpesa_password(shortcode: str, passkey: str, timestamp: str) -> str:
    """Generates the base64 encoded password for Daraja API."""
    data_to_encode = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(data_to_encode.encode("utf-8")).decode("utf-8")


def generate_transaction_reference() -> str:
    """Generates unique TXN reference."""
    year = timezone.now().year
    count = Payment.objects.filter(initiated_at__year=year).count() + 1
    return f"TXN-{year}-{count:04d}"


def get_mpesa_access_token() -> str:
    """Fetches OAuth token from Safaricom."""
    if not settings.MPESA_CONSUMER_KEY or not settings.MPESA_CONSUMER_SECRET:
        logger.warning("M-Pesa credentials missing. Returning dummy token for local dev/tests.")
        return "dummy_token"
        
    url = f"{settings.MPESA_ENVIRONMENT_URL}/oauth/v1/generate?grant_type=client_credentials"
    try:
        response = requests.get(
            url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET), timeout=10
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch M-Pesa access token: {e}")
        raise ValidationError({"mpesa": "Payment gateway is currently unreachable. Try again later."})


@transaction.atomic
def initiate_mpesa_payment(booking: Booking, phone_number: str) -> Payment:
    """
    Initiates an STK Push to the user's phone for the requested booking.
    Records a PENDING payment locally.
    """
    if booking.status != BookingStatus.PENDING:
        raise ValidationError({"booking": f"Cannot pay for booking in {booking.status} state."})
        
    amount = int(booking.total_amount)
    if amount <= 0:
        raise ValidationError({"amount": "Payment amount must be greater than zero."})

    # Format phone number to 2547XXXXXXXX
    if phone_number.startswith("0"):
        phone_number = f"254{phone_number[1:]}"
    elif phone_number.startswith("+"):
        phone_number = phone_number[1:]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = generate_mpesa_password(settings.MPESA_SHORTCODE, settings.MPESA_PASSKEY, timestamp)
    
    # Payload for Safaricom
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": booking.booking_reference,
        "TransactionDesc": "LabSynch Equipment Booking",
    }
    
    # Initial PENDING payment record
    payment = Payment.objects.create(
        transaction_ref=generate_transaction_reference(),
        booking=booking,
        amount_paid=Decimal(str(amount)),
        payment_method=PaymentMethod.MPESA,
        mpesa_phone_number=phone_number,
        payment_status=PaymentStatus.PENDING,
    )
    
    access_token = get_mpesa_access_token()
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    # Send Request to Safaricom
    if access_token != "dummy_token":
        url = f"{settings.MPESA_ENVIRONMENT_URL}/mpesa/stkpush/v1/processrequest"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Store Daraja tracking ID
            payment.mpesa_checkout_request_id = data.get("CheckoutRequestID")
            payment.save(update_fields=["mpesa_checkout_request_id", "updated_at"])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push failed for booking {booking.id}: {e}")
            payment.payment_status = PaymentStatus.FAILED
            payment.save(update_fields=["payment_status", "updated_at"])
            raise ValidationError({"mpesa": "Failed to initiate M-Pesa prompt. Please try again."})
    else:
        # Local development / Testing mock flow
        payment.mpesa_checkout_request_id = f"ws_CO_{timestamp}_mock"
        payment.save(update_fields=["mpesa_checkout_request_id", "updated_at"])

    return payment


@transaction.atomic
def process_mpesa_callback(payload: dict):
    """
    Processes the Safaricom async webhook, updates the payment record, 
    and cascades changes to the Bookings status.
    """
    try:
        stk_callback = payload.get("Body", {}).get("stkCallback", {})
        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        
        if not checkout_request_id:
            logger.warning("Invalid callback structure received.")
            return

        # Lock payment row
        try:
            payment = Payment.objects.select_for_update().get(mpesa_checkout_request_id=checkout_request_id)
        except Payment.DoesNotExist:
            logger.warning(f"Payment with CheckoutRequestID {checkout_request_id} not found.")
            return
            
        if payment.payment_status != PaymentStatus.PENDING:
            logger.info(f"Payment {payment.id} already processed.")
            return
            
        payment.callback_response = payload
        payment.completed_at = timezone.now()

        # Safaricom ResultCode 0 denotes success
        if result_code == 0:
            payment.payment_status = PaymentStatus.SUCCESS
            
            # Extract actual receipt and amount from items array
            callback_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
            for item in callback_items:
                if item.get("Name") == "MpesaReceiptNumber":
                    payment.mpesa_transaction_id = str(item.get("Value"))
            
            payment.save(
                update_fields=[
                    "payment_status", "mpesa_transaction_id", "completed_at", "callback_response", "updated_at"
                ]
            )
            
            # Cascade success to Booking
            booking = payment.booking
            booking.status = BookingStatus.PAID
            booking.save(update_fields=["status", "updated_at"])

            logger.info(f"Booking {booking.booking_reference} marked PAID via M-Pesa tx {payment.mpesa_transaction_id}")

            from apps.notifications.tasks import send_payment_receipt
            send_payment_receipt.delay(str(payment.id))
            
        else:
            # ResultCode != 0 means cancelled, insufficient funds, timeout, etc.
            payment.payment_status = PaymentStatus.FAILED
            payment.save(update_fields=["payment_status", "completed_at", "callback_response", "updated_at"])
            logger.info(f"M-Pesa payment failed for {payment.transaction_ref}. Reason: {stk_callback.get('ResultDesc')}")
            
    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {e}", exc_info=True)
        # We catch everything so Safaricom receives a 200 OK consistently
        # as failing to return 200 makes their servers retry pointlessly
