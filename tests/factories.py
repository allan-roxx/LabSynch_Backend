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
