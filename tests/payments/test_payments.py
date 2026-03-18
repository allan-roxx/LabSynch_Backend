import json
from unittest.mock import patch
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking, BookingStatus
from apps.payments.models import Payment, PaymentStatus
from tests.factories import SchoolProfileFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_data(db):
    user = UserFactory(email="school@example.com")
    profile = SchoolProfileFactory(user=user)
    
    booking = Booking.objects.create(
        booking_reference="BK-TEST-0001",
        school_profile=profile,
        pickup_date="2026-05-01",
        return_date="2026-05-05",
        status=BookingStatus.PENDING,
        total_amount="1500.00",
    )
    return {"user": user, "booking": booking}


@pytest.mark.django_db
class TestPaymentInitiation:
    @patch('apps.payments.services.requests.post')
    @patch('apps.payments.services.get_mpesa_access_token')
    def test_stk_push_initiation(self, mock_get_token, mock_post, api_client, setup_data):
        user = setup_data["user"]
        booking = setup_data["booking"]
        
        # Mocking responses
        mock_get_token.return_value = "mocked_auth_token"
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "MerchantRequestID": "29115-34620561-1",
            "CheckoutRequestID": "ws_CO_191220191020105958",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing"
        }
        
        # Login
        res = api_client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        url = reverse("payment-mpesa-stk-push")
        payload = {"booking_id": str(booking.id), "phone_number": "0712345678"}
        
        response = api_client.post(url, payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        
        payment = Payment.objects.get(id=response.data["data"]["payment_id"])
        assert payment.payment_status == PaymentStatus.PENDING
        assert payment.mpesa_checkout_request_id == "ws_CO_191220191020105958"
        assert payment.amount_paid == 1500.00


@pytest.mark.django_db
class TestPaymentCallback:
    def test_successful_mpesa_callback_updates_models(self, api_client, setup_data):
        booking = setup_data["booking"]
        
        # Setup pending payment
        payment = Payment.objects.create(
            transaction_ref="TXN-2026-0001",
            booking=booking,
            amount_paid="1500.00",
            payment_status=PaymentStatus.PENDING,
            mpesa_checkout_request_id="ws_CO_191220191020105958"
        )
        
        url = reverse("mpesa-callback")
        
        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-34620561-1",
                    "CheckoutRequestID": "ws_CO_191220191020105958",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 1500.00},
                            {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT61SV"},
                            {"Name": "Balance"},
                            {"Name": "TransactionDate", "Value": 20191219102115},
                            {"Name": "PhoneNumber", "Value": 254712345678}
                        ]
                    }
                }
            }
        }
        
        response = api_client.post(url, callback_payload, format="json")
        
        # Callback is public and returns 200 to Safaricom
        assert response.status_code == status.HTTP_200_OK
        
        # Verify Payment and Booking cascaded status changes
        payment.refresh_from_db()
        booking.refresh_from_db()
        
        assert payment.payment_status == PaymentStatus.SUCCESS
        assert payment.mpesa_transaction_id == "NLJ7RT61SV"
        assert booking.status == BookingStatus.PAID
