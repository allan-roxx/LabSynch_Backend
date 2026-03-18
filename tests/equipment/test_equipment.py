"""
Tests for Equipment & Inventory endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.equipment.models import Equipment, EquipmentCategory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(api_client, db, django_user_model):
    user = django_user_model.objects.create_superuser(
        email="admin@example.com", 
        password="TestPass123!",
        full_name="Admin Admin"
    )
    res = api_client.post(reverse("auth-login"), {"email": user.email, "password": "TestPass123!"})
    token = res.data["data"]["tokens"]["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.mark.django_db
class TestEquipment:
    def test_create_category(self, admin_client):
        url = reverse("category-list")
        res = admin_client.post(url, {"category_name": "Microscopes", "display_order": 1})
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["success"] is True

    def test_create_equipment_sets_available_qty(self, admin_client):
        # Create Category
        cat_res = admin_client.post(reverse("category-list"), {"category_name": "Lab Tools"})
        category_id = cat_res.data["data"]["id"]

        # Create Equipment
        url = reverse("equipment-list")
        payload = {
            "category": category_id,
            "equipment_name": "Test Microscope",
            "equipment_code": "TEST-MIC-01",
            "total_quantity": 10,
            "unit_price_per_day": "500.00",
            "condition": "NEW",
            "is_active": True
        }
        res = admin_client.post(url, payload)
        
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["success"] is True
        
        # Verify available_quantity matches total_quantity via initial create
        equipment = Equipment.objects.get(equipment_code="TEST-MIC-01")
        assert equipment.available_quantity == 10
        assert equipment.total_quantity == 10
