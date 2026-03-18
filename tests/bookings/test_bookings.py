"""
Tests for Bookings module focusing on complex services logic.
"""

from datetime import timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking, BookingStatus
from apps.equipment.models import Equipment, EquipmentCategory
from tests.factories import SchoolProfileFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_data(db):
    """Setup categories, equipment and users."""
    user = UserFactory(email="school@example.com")
    SchoolProfileFactory(user=user)
    
    cat = EquipmentCategory.objects.create(category_name="Microscopes")
    eq1 = Equipment.objects.create(
        category=cat,
        equipment_name="Basic Microscope",
        equipment_code="MIC-001",
        total_quantity=5,
        available_quantity=5,
        unit_price_per_day="100.00",
    )
    return {"user": user, "equipment": eq1}


@pytest.mark.django_db
class TestBookingCreation:
    def test_booking_decreases_available_quantity(self, api_client, setup_data):
        user = setup_data["user"]
        equipment = setup_data["equipment"]
        
        # Login
        res = api_client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
        token = res.data["data"]["tokens"]["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        
        pickup = timezone.now().date() + timedelta(days=1)
        ret = pickup + timedelta(days=3)
        
        payload = {
            "pickup_date": str(pickup),
            "return_date": str(ret),
            "items": [
                {"equipment": str(equipment.id), "quantity": 2}
            ]
        }
        
        response = api_client.post(reverse("booking-list"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        
        # Check available quantity is updated
        equipment.refresh_from_db()
        assert equipment.available_quantity == 3
        assert equipment.total_quantity == 5
        
        booking = Booking.objects.get(id=response.data["data"]["id"])
        assert booking.status == BookingStatus.PENDING
        assert booking.booking_items.count() == 1

    def test_overbooking_prevented(self, api_client, setup_data):
        user = setup_data["user"]
        equipment = setup_data["equipment"]
        
        # Login
        res = api_client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        pickup = timezone.now().date() + timedelta(days=1)
        ret = pickup + timedelta(days=3)
        
        # Request 6 items (only 5 available total)
        payload = {
            "pickup_date": str(pickup),
            "return_date": str(ret),
            "items": [{"equipment": str(equipment.id), "quantity": 6}]
        }
        
        response = api_client.post(reverse("booking-list"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False
        assert "Only 5" in response.data["errors"]["quantity"][0]

        # Ensure no booking was created
        assert Booking.objects.count() == 0
        equipment.refresh_from_db()
        assert equipment.available_quantity == 5


@pytest.mark.django_db
class TestBookingCancellation:
    def test_cancel_booking_restores_quantity(self, api_client, setup_data):
        user = setup_data["user"]
        equipment = setup_data["equipment"]
        
        # Login
        res = api_client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        pickup = timezone.now().date() + timedelta(days=1)
        ret = pickup + timedelta(days=3)
        
        # Create booking for 3 items
        payload = {
            "pickup_date": str(pickup),
            "return_date": str(ret),
            "items": [{"equipment": str(equipment.id), "quantity": 3}]
        }
        res = api_client.post(reverse("booking-list"), payload, format="json")
        booking_id = res.data["data"]["id"]
        
        equipment.refresh_from_db()
        assert equipment.available_quantity == 2
        
        # Cancel booking
        cancel_url = reverse("booking-cancel", args=[booking_id])
        cancel_res = api_client.post(cancel_url)
        
        assert cancel_res.status_code == status.HTTP_200_OK
        
        booking = Booking.objects.get(id=booking_id)
        assert booking.status == BookingStatus.CANCELLED
        
        # Quantity should be restored
        equipment.refresh_from_db()
        assert equipment.available_quantity == 5
