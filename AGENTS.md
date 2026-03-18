# AGENTS.md — LabSynch Django REST API

This file defines the standards, conventions, and rules all agents must follow when contributing to the LabSynch codebase. Read this file in full before writing or modifying any code.

---

## 1. Project Overview

LabSynch is a multi-tenant laboratory equipment rental and management platform built with:

- **Backend:** Django + Django REST Framework (DRF)
- **Database:** PostgreSQL via Django ORM
- **Auth:** JWT (via `djangorestframework-simplejwt`)
- **Async:** Celery + Redis
- **Payments:** M-Pesa Daraja API
- **Storage:** S3-compatible object storage

The two primary actor types are `SCHOOL` users and `ADMIN` users. All agents must respect this role boundary in every feature they implement.

---

## 2. Language & Naming Conventions

### 2.1 General Casing Rules

| Context | Convention | Example |
|---|---|---|
| Python variables | `snake_case` | `booking_status` |
| Python functions | `snake_case` | `get_available_quantity()` |
| Python classes | `PascalCase` | `BookingSerializer` |
| Django models | `PascalCase` | `EquipmentCategory` |
| Django model fields | `snake_case` | `pickup_date`, `is_active` |
| URL path segments | `kebab-case` | `/api/booking-items/` |
| JSON request/response keys | `snake_case` | `"return_date"`, `"school_profile"` |
| Constants / enums (Python) | `UPPER_SNAKE_CASE` | `BOOKING_STATUS_PENDING` |
| Environment variables | `UPPER_SNAKE_CASE` | `MPESA_CONSUMER_KEY` |
| Celery task names | `snake_case` dotted | `notifications.send_booking_confirmation` |

### 2.2 Model Naming

- Model names are always **singular** nouns: `Booking`, not `Bookings`.
- Related manager names follow Django defaults but must be explicit in `related_name`:
  ```python
  school_profile = models.ForeignKey(
      SchoolProfile,
      on_delete=models.PROTECT,
      related_name="bookings",
  )
  ```

### 2.3 File & Module Naming

| What | Convention | Example |
|---|---|---|
| Django apps | `snake_case` | `bookings/`, `equipment/` |
| Python files | `snake_case` | `serializers.py`, `booking_utils.py` |
| Test files | `test_<module>.py` | `test_booking_service.py` |
| Migration files | Auto-generated only — never rename | `0003_add_overdue_status.py` |

---

## 3. Project Structure

```
labsynch/
├── config/                   # Django project config (settings, urls, wsgi, asgi)
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── authentication/       # JWT auth, registration, email verification
│   ├── users/                # USER model, SCHOOL_PROFILE
│   ├── equipment/            # EquipmentCategory, Equipment, EquipmentImage
│   ├── bookings/             # Booking, BookingItem, availability logic
│   ├── payments/             # Payment, M-Pesa integration
│   ├── issuances/            # EquipmentIssuance, EquipmentReturn
│   ├── damages/              # DamageReport
│   ├── maintenance/          # MaintenanceSchedule
│   ├── notifications/        # Notification model, Celery tasks
│   ├── audit/                # AuditLog
│   ├── reports/              # Reporting views (admin only)
│   └── settings_app/         # SystemSetting, PricingRule
├── common/                   # Shared utils, base classes, mixins, exceptions
│   ├── exceptions.py
│   ├── pagination.py
│   ├── permissions.py
│   └── utils.py
├── tests/                    # Mirror app structure
│   ├── bookings/
│   ├── payments/
│   └── ...
├── .env.example
├── manage.py
└── requirements/
    ├── base.txt
    ├── development.txt
    └── production.txt
```

Each Django app must contain:
```
<app>/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── services.py       # Business logic — never put it in views or models
├── permissions.py    # App-specific permission classes (if needed)
└── tasks.py          # Celery tasks (if needed)
```

---

## 4. Models

### 4.1 Base Model

All models must inherit from a shared `BaseModel`:

```python
# common/models.py
import uuid
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

**Rules:**
- All models use `UUIDField` as the primary key — never integer PKs.
- Never use `auto_now_add=True` outside of `BaseModel`; always go through inheritance.
- Add `class Meta: ordering` where default ordering is meaningful (e.g., `-created_at`).

### 4.2 Soft Deletion

Never hard-delete core business entities. Use `is_active`:

```python
is_active = models.BooleanField(default=True)
```

Provide a `deactivate()` method on models where applicable:

```python
def deactivate(self):
    self.is_active = False
    self.save(update_fields=["is_active", "updated_at"])
```

### 4.3 Status Fields

All status fields must use `models.TextChoices`:

```python
class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    PAID = "PAID", "Paid"
    ISSUED = "ISSUED", "Issued"
    RETURNED = "RETURNED", "Returned"
    OVERDUE = "OVERDUE", "Overdue"
    CANCELLED = "CANCELLED", "Cancelled"

status = models.CharField(
    max_length=20,
    choices=BookingStatus.choices,
    default=BookingStatus.PENDING,
)
```

### 4.4 Reference Fields

Human-readable references (e.g., `BK-2025-0001`) are generated in the **service layer**, never in views or serializers:

```python
# bookings/services.py
def generate_booking_reference() -> str:
    year = timezone.now().year
    count = Booking.objects.filter(created_at__year=year).count() + 1
    return f"BK-{year}-{count:04d}"
```

---

## 5. Services Layer

All business logic lives in `services.py`. Views and serializers must not contain business logic.

### 5.1 Service Function Signature

```python
# bookings/services.py
from django.db import transaction
from .models import Booking, BookingItem
from apps.equipment.models import Equipment


@transaction.atomic
def create_booking(
    school_profile,
    equipment_items: list[dict],
    pickup_date,
    return_date,
) -> Booking:
    """
    Creates a booking with line items and reserves equipment availability.
    Raises ValidationError on constraint violations.
    """
    ...
```

**Rules:**
- All functions that touch booking/payment/inventory together must be wrapped in `@transaction.atomic`.
- Services raise `django.core.exceptions.ValidationError` or custom exceptions from `common/exceptions.py` — never HTTP exceptions.
- Views catch service exceptions and map them to DRF responses.
- Services are unit-testable in isolation.

---

## 6. Serializers

### 6.1 General Rules

- Use `ModelSerializer` as the base unless you have a strong reason not to.
- Separate **read** and **write** serializers when the shapes differ significantly:
  ```
  BookingReadSerializer     # for GET responses
  BookingCreateSerializer   # for POST request validation
  ```
- Never expose internal fields (e.g., `id` is fine; raw FK integer IDs should be represented as UUIDs).
- Use `SerializerMethodField` for computed values only — do not run queries inside them without `select_related`/`prefetch_related` being set on the queryset.

### 6.2 Validation

All field-level constraints go in serializer `validate_<field>` methods. Cross-field validation goes in `validate()`:

```python
def validate(self, attrs):
    if attrs["return_date"] <= attrs["pickup_date"]:
        raise serializers.ValidationError(
            {"return_date": "Return date must be after pickup date."}
        )
    return attrs
```

---

## 7. Views & ViewSets

- Prefer `ModelViewSet` for standard CRUD; use `APIView` or `GenericAPIView` for non-CRUD endpoints (e.g., payment callbacks).
- Views must only: authenticate, authorize, deserialize input, call a service, serialize output.
- No business logic in views — delegate entirely to `services.py`.
- All viewsets must declare explicit `permission_classes` — never rely on global defaults alone.

```python
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingReadSerializer
    permission_classes = [IsAuthenticated, IsSchoolUser]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return Booking.objects.filter(
            school_profile__user=self.request.user
        ).select_related("school_profile").prefetch_related("booking_items")
```

---

## 8. URL Configuration

### 8.1 URL Patterns

All API routes are prefixed with `/api/`. Use DRF routers for viewsets:

```python
# apps/bookings/urls.py
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")

urlpatterns = router.urls
```

```python
# config/urls.py
urlpatterns = [
    path("api/", include("apps.bookings.urls")),
    path("api/", include("apps.equipment.urls")),
    # ...
]
```

### 8.2 URL Segment Rules

- Always `kebab-case`: `/api/equipment-categories/`, `/api/booking-items/`
- Nested resources use a flat URL with a filter param where possible; only nest one level deep when semantically required:
  - Preferred: `GET /api/booking-items/?booking=<uuid>`
  - Acceptable: `GET /api/bookings/<uuid>/items/`

---

## 9. API Response Format

Every API response must conform to the following envelope structure. No exceptions.

### 9.1 Success Response

```json
{
  "success": true,
  "message": "Booking created successfully.",
  "data": {
    "id": "3f9a1c2e-7b4d-4e8a-a12b-9f0c3d2e5a7b",
    "reference": "BK-2025-0042",
    "status": "PENDING",
    "pickup_date": "2025-08-01",
    "return_date": "2025-08-05",
    "total_amount": "15000.00",
    "school_profile": {
      "id": "a1b2c3d4-...",
      "school_name": "Nairobi Academy"
    },
    "booking_items": [
      {
        "id": "...",
        "equipment_name": "Bunsen Burner",
        "quantity": 3,
        "unit_price": "2500.00",
        "subtotal": "7500.00"
      }
    ],
    "created_at": "2025-07-15T10:30:00Z"
  }
}
```

### 9.2 Paginated List Response

```json
{
  "success": true,
  "message": "Bookings retrieved successfully.",
  "data": {
    "count": 87,
    "next": "https://api.labsynch.co.ke/api/bookings/?page=3",
    "previous": "https://api.labsynch.co.ke/api/bookings/?page=1",
    "results": [ ]
  }
}
```

### 9.3 Error Response

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "return_date": ["Return date must be after pickup date."],
    "quantity": ["Requested quantity exceeds available stock."]
  }
}
```

For non-field errors (e.g., business rule violations):

```json
{
  "success": false,
  "message": "Booking cannot be cancelled in its current state.",
  "errors": {
    "non_field_errors": ["Booking cannot be cancelled in its current state."]
  }
}
```

### 9.4 Response Rules

- `success`: always a boolean.
- `message`: always a human-readable string. Never null.
- `data`: present on success, absent on error.
- `errors`: present on error, absent on success.
- HTTP status codes must match:

| Scenario | Status Code |
|---|---|
| Successful GET / list | 200 |
| Successful POST (create) | 201 |
| Successful action (non-create) | 200 |
| Validation error | 400 |
| Unauthenticated | 401 |
| Forbidden (wrong role) | 403 |
| Resource not found | 404 |
| Conflict (e.g., double booking) | 409 |
| Server error | 500 |

### 9.5 Custom Response Renderer

Implement a custom DRF renderer/exception handler in `common/` to enforce this envelope consistently — do not manually build the envelope in every view.

```python
# common/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "message": "An error occurred.",
            "errors": response.data,
        }
    return response
```

---

## 10. Permissions

### 10.1 Custom Permission Classes

Define in `common/permissions.py`:

```python
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == "ADMIN"


class IsSchoolUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == "SCHOOL"
```

- Always apply permissions at the `ViewSet` level with `permission_classes`.
- Use `get_permissions()` when a single viewset has different rules per action:
  ```python
  def get_permissions(self):
      if self.action in ["list", "retrieve"]:
          return [IsAuthenticated()]
      return [IsAuthenticated(), IsAdminUser()]
  ```

---

## 11. Authentication

- Use JWT. Access token lifetime: 60 minutes. Refresh token lifetime: 7 days.
- All endpoints require `Authorization: Bearer <token>` except: registration, login, M-Pesa callback, and the public equipment catalog.
- Email verification is required before a `SCHOOL` user can create a booking.

---

## 12. Database & Query Rules

- Always use `select_related()` for FK/OneToOne fields accessed in a serializer.
- Always use `prefetch_related()` for reverse FK or M2M fields accessed in a serializer.
- Never run queries inside a loop — this is a hard rule. Use `bulk_create`, `bulk_update`, or querysets.
- Use `update_fields=["field1", "field2"]` on `save()` whenever you are not saving the full model.
- Use `F()` expressions for atomic numeric updates (e.g., decrementing available quantity):
  ```python
  Equipment.objects.filter(pk=equipment_id).update(
      available_quantity=F("available_quantity") - quantity
  )
  ```
- Apply `select_for_update()` inside transactions when reading then writing inventory quantities to prevent race conditions.

---

## 13. Celery Tasks

- All tasks live in `<app>/tasks.py`.
- Tasks must be idempotent wherever possible.
- Tasks must never perform direct DB writes that should be in a transaction with a view action — use signals or pass IDs, not model instances.
- Name tasks explicitly:

```python
# notifications/tasks.py
from config.celery import app


@app.task(name="notifications.send_booking_confirmation", bind=True, max_retries=3)
def send_booking_confirmation(self, booking_id: str):
    ...
```

---

## 14. Environment & Settings

- All secrets and environment-specific values go in `.env` (never committed).
- Access via `django-environ` or `os.environ.get()` with a clear default or hard failure.
- `settings/base.py` holds shared config. `development.py` and `production.py` import from base and override.
- Debug mode must be `False` in production — enforced via env var.

```python
# config/settings/base.py
import environ

env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY")
MPESA_CONSUMER_KEY = env("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = env("MPESA_CONSUMER_SECRET")
```

---

## 15. Error Handling Rules

- Services raise `ValidationError` or domain-specific exceptions from `common/exceptions.py`.
- Views never swallow exceptions silently.
- All M-Pesa callback processing must be wrapped in `try/except` and fully logged before returning a `200 OK` to Safaricom's server.
- Unexpected exceptions are logged via Django's logging framework (not `print()`).

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Booking %s created for school %s", booking.reference, school_profile.id)
logger.error("M-Pesa callback processing failed: %s", str(exc), exc_info=True)
```

---

## 16. Testing

- Every service function must have unit tests in `tests/<app>/test_<module>.py`.
- Use `pytest` with `pytest-django`.
- Use `factory_boy` for model factories — never create test data inline with `Model.objects.create()` scattered across tests.
- Aim for: **services = 90%+ coverage**, **views = happy-path + error-path per endpoint**.
- Payment and M-Pesa callback tests must mock the external HTTP call.

```python
# tests/bookings/test_booking_service.py
import pytest
from apps.bookings.services import create_booking
from tests.factories import SchoolProfileFactory, EquipmentFactory


@pytest.mark.django_db
def test_create_booking_reserves_availability():
    school = SchoolProfileFactory()
    equipment = EquipmentFactory(available_quantity=5)
    ...
```

---

## 17. Git & Commit Conventions

- Branch naming: `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- Commit messages follow Conventional Commits:
  ```
  feat(bookings): add overdue status transition logic
  fix(payments): handle duplicate mpesa callback gracefully
  chore(deps): upgrade djangorestframework to 3.15
  ```
- No direct commits to `main`. All changes go through a pull request.
- PR must include: what changed, why, and any migration notes.

---

## 18. What Agents Must Never Do

- ❌ Put business logic in views or serializers.
- ❌ Use integer primary keys on any model.
- ❌ Hard-delete core business entities (`Booking`, `Equipment`, `Payment`, etc.).
- ❌ Run raw SQL unless there is no ORM equivalent and it is clearly documented.
- ❌ Return raw DRF responses without the standard envelope format.
- ❌ Expose internal exception tracebacks in API responses.
- ❌ Commit secrets, `.env` files, or credentials of any kind.
- ❌ Write queries inside loops.
- ❌ Skip `@transaction.atomic` on any operation touching booking + inventory + payment together.
- ❌ Use `print()` for logging — always use the `logging` module.
- ❌ Create migrations manually — always run `python manage.py makemigrations`.

---

## 19. Key Business Constraint Reminders

These constraints must be enforced at the **service layer** AND as **DB constraints** where possible:

- `available_quantity >= 0` and `<= total_quantity`
- `return_date > pickup_date`
- Booking `status` transitions must follow the defined state machine — no arbitrary jumps.
- Payment amounts must be positive.
- Booking and payment references must be unique (enforce with `unique=True` on the model field).
- `OVERDUE` is a valid booking status — include it in the `BookingStatus` enum from day one.

---

*Last updated: project kickoff. Any agent modifying this file must note the change in the PR description.*