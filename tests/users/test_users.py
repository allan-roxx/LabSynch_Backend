"""
Tests for the Users app service layer.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.users.models import AccountStatus
from apps.users.services import (
    admin_update_school_profile,
    change_password,
    update_school_profile,
    update_user_profile,
)
from tests.factories import SchoolProfileFactory, UserFactory


@pytest.mark.django_db
def test_update_user_full_name():
    user = UserFactory(full_name="Old Name")
    updated = update_user_profile(user, full_name="New Name")
    assert updated.full_name == "New Name"
    updated.refresh_from_db()
    assert updated.full_name == "New Name"


@pytest.mark.django_db
def test_update_user_phone_number():
    user = UserFactory(phone_number="0700000000")
    updated = update_user_profile(user, phone_number="0711111111")
    assert updated.phone_number == "0711111111"
    updated.refresh_from_db()
    assert updated.phone_number == "0711111111"


@pytest.mark.django_db
def test_update_user_no_kwargs_is_safe():
    user = UserFactory(full_name="Unchanged")
    updated = update_user_profile(user)
    assert updated.full_name == "Unchanged"


@pytest.mark.django_db
def test_update_school_profile_name_and_county():
    profile = SchoolProfileFactory(school_name="Old School", county="Nairobi")
    updated = update_school_profile(profile, {"school_name": "New School", "county": "Mombasa"})
    assert updated.school_name == "New School"
    assert updated.county == "Mombasa"
    updated.refresh_from_db()
    assert updated.school_name == "New School"


@pytest.mark.django_db
def test_update_school_profile_ignores_sensitive_fields():
    """SCHOOL update must silently drop account_status and credit_limit."""
    profile = SchoolProfileFactory(account_status=AccountStatus.ACTIVE, credit_limit=0)
    update_school_profile(
        profile,
        {
            "school_name": "Legit Change",
            "account_status": AccountStatus.BLOCKED,
            "credit_limit": 99999,
        },
    )
    profile.refresh_from_db()
    assert profile.account_status == AccountStatus.ACTIVE
    assert profile.credit_limit == 0
    assert profile.school_name == "Legit Change"


@pytest.mark.django_db
def test_admin_update_school_profile_status():
    profile = SchoolProfileFactory(account_status=AccountStatus.ACTIVE)
    updated = admin_update_school_profile(profile, {"account_status": AccountStatus.SUSPENDED})
    assert updated.account_status == AccountStatus.SUSPENDED
    updated.refresh_from_db()
    assert updated.account_status == AccountStatus.SUSPENDED


@pytest.mark.django_db
def test_admin_update_school_profile_credit_limit():
    profile = SchoolProfileFactory(credit_limit=0)
    updated = admin_update_school_profile(profile, {"credit_limit": 50000})
    assert updated.credit_limit == 50000
    updated.refresh_from_db()
    assert updated.credit_limit == 50000


@pytest.mark.django_db
def test_change_password_success():
    user = UserFactory()
    change_password(user, "TestPass123!", "NewSecurePass789!")
    user.refresh_from_db()
    assert user.check_password("NewSecurePass789!")
    assert not user.check_password("TestPass123!")


@pytest.mark.django_db
def test_change_password_wrong_old_password_raises():
    user = UserFactory()
    with pytest.raises(ValidationError) as exc_info:
        change_password(user, "WrongPassword!", "NewPass789!")
    assert "old_password" in exc_info.value.message_dict
