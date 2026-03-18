import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.bookings.models import Booking, BookingItem, BookingStatus
from apps.damages.models import DamageReport, DamageSeverity, ResolutionStatus
from apps.equipment.models import Equipment, EquipmentCategory
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
    
    category = EquipmentCategory.objects.create(category_name="Lab Tools")
    equipment = Equipment.objects.create(
        category=category,
        equipment_name="Microscope",
        equipment_code="MIC-001",
        total_quantity=10,
        available_quantity=9,
        unit_price_per_day="750.00"
    )
    
    booking = Booking.objects.create(
        booking_reference="BK-TEST-0001",
        school_profile=school_profile,
        pickup_date="2026-05-01",
        return_date="2026-05-05",
        status=BookingStatus.COMPLETED,
        total_amount="1500.00",
    )
    
    booking_item = BookingItem.objects.create(
        booking=booking,
        equipment=equipment,
        quantity=1,
        unit_price="750.00",
        subtotal="1500.00"
    )
    
    # We need a return record to attach the damage to
    EquipmentIssuance.objects.create(booking=booking, issued_by=admin_user, received_by=school_user)
    equipment_return = EquipmentReturn.objects.create(booking=booking, received_by=admin_user, returned_by=school_user, has_damage=True)
    
    return {
        "school": school_user,
        "admin": admin_user,
        "booking_item": booking_item,
        "equipment_return": equipment_return
    }


@pytest.mark.django_db
class TestDamageReports:
    
    def test_admin_can_create_and_resolve_damage_report(self, api_client, setup_data):
        admin = setup_data["admin"]
        booking_item = setup_data["booking_item"]
        equipment_return = setup_data["equipment_return"]
        
        # Login admin
        res = api_client.post(reverse("auth-login"), {"email": admin.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        # 1. Create Damage Report
        url = reverse("damage-list")
        payload = {
            "equipment_return": str(equipment_return.id),
            "booking_item": str(booking_item.id),
            "quantity_damaged": 1,
            "severity": DamageSeverity.MODERATE,
            "description": "Lens scratched upon return."
        }
        
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        report_id = response.data["data"]["id"]
        report = DamageReport.objects.get(id=report_id)
        assert report.severity == DamageSeverity.MODERATE
        assert report.resolution_status == ResolutionStatus.PENDING

        # 2. Resolve Damage Report
        resolve_url = reverse("damage-resolve", args=[report_id])
        resolve_payload = {
            "resolution_status": ResolutionStatus.CHARGED,
            "repair_cost": "250.00"
        }
        
        resolve_response = api_client.post(resolve_url, resolve_payload, format="json")
        assert resolve_response.status_code == status.HTTP_200_OK
        
        report.refresh_from_db()
        assert report.resolution_status == ResolutionStatus.CHARGED
        assert report.repair_cost == 250.00
