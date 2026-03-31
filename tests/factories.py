"""
Factories for test data using factory_boy.
"""

import factory
from django.contrib.auth.hashers import make_password

from apps.users.models import AccountStatus, SchoolProfile, User, UserType


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances in tests."""

    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    phone_number = factory.Faker("phone_number")
    user_type = UserType.SCHOOL
    is_verified = True
    password = factory.LazyFunction(lambda: make_password("TestPass123!"))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to use create_user for proper password hashing."""
        password = kwargs.pop("password", "TestPass123!")
        # If password is already hashed (from LazyFunction), use it directly
        if password.startswith("pbkdf2_") or password.startswith("bcrypt"):
            user = super()._create(model_class, *args, password=password, **kwargs)
        else:
            manager = cls._get_manager(model_class)
            user = manager.create_user(password=password, *args, **kwargs)
        return user


class SchoolProfileFactory(factory.django.DjangoModelFactory):
    """Factory for creating SchoolProfile instances in tests."""

    class Meta:
        model = SchoolProfile

    user = factory.SubFactory(UserFactory)
    school_name = factory.Faker("company")
    registration_number = factory.Sequence(lambda n: f"REG-{n:04d}")
    physical_address = factory.Faker("address")
    county = factory.Faker("city")
    contact_person = factory.Faker("name")
    contact_designation = "Head of Science"
    credit_limit = 0
    account_status = AccountStatus.ACTIVE


# ---------------------------------------------------------------------------
# Equipment factories
# ---------------------------------------------------------------------------

from datetime import date, timedelta
from decimal import Decimal

from apps.bookings.models import Booking, BookingStatus
from apps.equipment.models import Equipment, EquipmentCategory
from apps.payments.models import Payment, PaymentMethod, PaymentStatus


class EquipmentCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EquipmentCategory

    category_name = factory.Sequence(lambda n: f"Test Category {n}")
    description = "Test category"
    display_order = factory.Sequence(lambda n: n)


class EquipmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Equipment

    category = factory.SubFactory(EquipmentCategoryFactory)
    equipment_name = factory.Sequence(lambda n: f"Equipment {n}")
    equipment_code = factory.Sequence(lambda n: f"EQ-{n:04d}")
    description = "Test equipment"
    total_quantity = 10
    available_quantity = 10
    unit_price_per_day = Decimal("500.00")
    condition = "GOOD"
    is_active = True


class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Booking

    booking_reference = factory.Sequence(lambda n: f"BK-2026-{n:04d}")
    school_profile = factory.SubFactory(SchoolProfileFactory)
    pickup_date = factory.LazyFunction(lambda: date.today() + timedelta(days=1))
    return_date = factory.LazyFunction(lambda: date.today() + timedelta(days=5))
    status = BookingStatus.PENDING
    total_amount = Decimal("5000.00")
    special_instructions = ""


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    transaction_ref = factory.Sequence(lambda n: f"TXN-2026-{n:04d}")
    booking = factory.SubFactory(BookingFactory, status=BookingStatus.PAID)
    amount_paid = Decimal("5000.00")
    payment_method = PaymentMethod.MPESA
    payment_status = PaymentStatus.SUCCESS
    mpesa_transaction_id = factory.Sequence(lambda n: f"MPESA{n:08d}")
    mpesa_phone_number = "254700000000"
