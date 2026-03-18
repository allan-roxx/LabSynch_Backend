import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.equipment.models import Equipment, EquipmentCategory
from apps.maintenance.models import MaintenanceSchedule, MaintenanceStatus, MaintenanceType
from tests.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_data(db):
    admin_user = UserFactory(email="admin@example.com", user_type="ADMIN")
    
    category = EquipmentCategory.objects.create(category_name="Lab Tools")
    equipment = Equipment.objects.create(
        category=category,
        equipment_name="Microscope",
        equipment_code="MIC-001",
        total_quantity=10,
        available_quantity=10,
        unit_price_per_day="750.00"
    )
    
    return {
        "admin": admin_user,
        "equipment": equipment
    }


@pytest.mark.django_db
class TestMaintenanceSchedules:
    
    def test_admin_can_schedule_and_complete_maintenance(self, api_client, setup_data):
        admin = setup_data["admin"]
        equipment = setup_data["equipment"]
        
        # Login admin
        res = api_client.post(reverse("auth-login"), {"email": admin.email, "password": "TestPass123!"})
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['data']['tokens']['access']}")
        
        # 1. Schedule Maintenance
        url = reverse("maintenance-list")
        payload = {
            "equipment": str(equipment.id),
            "maintenance_type": MaintenanceType.ROUTINE,
            "description": "Quarterly calibration and lens cleaning.",
            "scheduled_date": "2026-06-01"
        }
        
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        
        schedule_id = response.data["data"]["id"]
        schedule = MaintenanceSchedule.objects.get(id=schedule_id)
        assert schedule.status == MaintenanceStatus.SCHEDULED

        # 2. Update to Completed with Costs
        update_url = reverse("maintenance-detail", args=[schedule_id])
        update_payload = {
            "status": MaintenanceStatus.COMPLETED,
            "technician_name": "John Doe",
            "cost": "150.00",
            "notes": "Lens replaced."
        }
        
        update_response = api_client.patch(update_url, update_payload, format="json")
        assert update_response.status_code == status.HTTP_200_OK
        
        schedule.refresh_from_db()
        assert schedule.status == MaintenanceStatus.COMPLETED
        assert schedule.cost == 150.00
        assert schedule.completed_date is not None
