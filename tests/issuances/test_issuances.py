import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking, BookingItem, BookingStatus
from apps.equipment.models import Equipment
from apps.issuances.models import EquipmentIssuance, EquipmentReturn
from tests.factories import SchoolProfileFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_data(db):
    school_user = UserFactory(email="school@example.com", user_type="SCHOOL")
    school_profile = SchoolProfileFactory(user=school_user)
    
    admin_user = UserFactory(email="admin@example.com", user_type="ADMIN")
    
    from apps.equipment.models import EquipmentCategory
    category = EquipmentCategory.objects.create(category_name="Lab Tools")
    
    # Create Equipment
    equipment = Equipment.objects.create(
        category=category,
        equipment_name="Microscope",
        equipment_code="MIC-001",
        total_quantity=10,
        available_quantity=8, # 2 are allegedly booked out
        unit_price_per_day="750.00"
    )
    
    # Create Booking
    booking = Booking.objects.create(
        booking_reference="BK-TEST-0001",
        school_profile=school_profile,
        pickup_date="2026-05-01",
        return_date="2026-05-05",
        status=BookingStatus.RESERVED,  # Must be RESERVED to issue
        total_amount="1500.00",
    )
    
    # Create Booking Item (Qty 2)
    BookingItem.objects.create(
        booking=booking,
        equipment=equipment,
        quantity=2,
        unit_price="750.00",
        subtotal="1500.00"
    )
    
    return {
        "school": school_user,
        "admin": admin_user,
        "booking": booking,
        "equipment": equipment
    }


@pytest.mark.django_db
class TestIssuancesAndReturns:
    
    def test_admin_can_issue_paid_booking(self, api_client, setup_data):
        admin = setup_data["admin"]
        booking = setup_data["booking"]
        school = setup_data["school"]
        
        # Login specific admin
        res = api_client.post(reverse("auth-login"), {"email": admin.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        url = reverse("issuance-list")
        payload = {
            "booking": str(booking.id),
            "received_by": str(school.id),
            "issue_notes": "Picked up physically."
        }
        
        response = api_client.post(url, payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert EquipmentIssuance.objects.filter(booking=booking).exists()
        
        # Verify Booking Status shifted from RESERVED to IN_USE
        booking.refresh_from_db()
        assert booking.status == BookingStatus.IN_USE

    def test_school_user_cannot_issue_equipment(self, api_client, setup_data):
        school = setup_data["school"]
        booking = setup_data["booking"]
        
        # Login specific school
        res = api_client.post(reverse("auth-login"), {"email": school.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        url = reverse("issuance-list")
        payload = {
            "booking": str(booking.id),
            "received_by": str(school.id)
        }
        
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_admin_can_return_issued_equipment_and_restore_inventory(self, api_client, setup_data):
        admin = setup_data["admin"]
        booking = setup_data["booking"]
        school = setup_data["school"]
        equipment = setup_data["equipment"]
        
        # Simulate already issued booking
        booking.status = BookingStatus.IN_USE
        booking.save()
        
        EquipmentIssuance.objects.create(booking=booking, issued_by=admin, received_by=school)
        
        assert equipment.available_quantity == 8
        
        # Login specific admin
        res = api_client.post(reverse("auth-login"), {"email": admin.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        url = reverse("return-list")
        payload = {
            "booking": str(booking.id),
            "returned_by": str(school.id),
            "return_notes": "All neat and clean.",
            "has_damage": False
        }
        
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify Booking Status shifted from IN_USE to RETURNED
        booking.refresh_from_db()
        assert booking.status == BookingStatus.RETURNED
        
        # Verify Equipment Quantity was restored (+2 quantity)
        equipment.refresh_from_db()
        assert equipment.available_quantity == 10
