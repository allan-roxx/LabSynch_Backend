"""
Tests for Equipment & Inventory endpoints.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.equipment.models import Equipment, EquipmentCategory


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xda\x1f\xb3\x00\x00\x00\x00IEND\xaeB`\x82"
)


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

    def test_add_stock_appends_total_and_available_quantities(self, admin_client):
        cat = EquipmentCategory.objects.create(category_name="Optics")
        equipment = Equipment.objects.create(
            category=cat,
            equipment_name="Projection Lens",
            equipment_code="OPT-001",
            total_quantity=4,
            available_quantity=4,
            unit_price_per_day="200.00",
        )

        url = reverse("equipment-add-stock", args=[equipment.id])
        res = admin_client.post(url, {"additional_quantity": 3}, format="json")

        assert res.status_code == status.HTTP_200_OK
        equipment.refresh_from_db()
        assert equipment.total_quantity == 7
        assert equipment.available_quantity == 7

    def test_upload_and_update_equipment_image(self, admin_client):
        cat = EquipmentCategory.objects.create(category_name="Chemistry")
        equipment = Equipment.objects.create(
            category=cat,
            equipment_name="Beaker Set",
            equipment_code="CHEM-001",
            total_quantity=8,
            available_quantity=8,
            unit_price_per_day="80.00",
        )

        upload_url = reverse("equipment-upload-image", args=[equipment.id])
        first_image = SimpleUploadedFile("first.png", PNG_BYTES, content_type="image/png")
        upload_res = admin_client.post(
            upload_url,
            {"image": first_image, "is_primary": "true", "display_order": 0},
            format="multipart",
        )

        assert upload_res.status_code == status.HTTP_201_CREATED
        image_id = upload_res.data["data"]["id"]
        assert upload_res.data["data"]["is_primary"] is True

        update_url = reverse("equipment-update-image", kwargs={"pk": equipment.id, "image_id": image_id})
        replacement = SimpleUploadedFile("replacement.png", PNG_BYTES, content_type="image/png")
        update_res = admin_client.patch(update_url, {"image": replacement}, format="multipart")

        assert update_res.status_code == status.HTTP_200_OK
        assert update_res.data["data"]["image_url"].startswith("http")
