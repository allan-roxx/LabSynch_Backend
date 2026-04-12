import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from common.models import BaseModel


class UserType(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    SCHOOL = "SCHOOL", "School"


class UserManager(BaseUserManager):
    """Custom manager for the User model using email as the identifier."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("user_type", UserType.ADMIN)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom user model for LabSynch.

    Uses email as the unique identifier instead of username.
    Supports two role types: ADMIN and SCHOOL.
    """

    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, default="")
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.SCHOOL,
    )
    is_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # Django auth fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])


class AccountStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    BLOCKED = "BLOCKED", "Blocked"


class LiabilityStatus(models.TextChoices):
    CLEAR = "CLEAR", "Clear"
    HAS_OUTSTANDING = "HAS_OUTSTANDING", "Has Outstanding Liabilities"


class SchoolProfile(BaseModel):
    """
    Extended profile for SCHOOL-type users.

    One-to-one relationship with User where user_type == 'SCHOOL'.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="school_profile",
    )
    school_name = models.CharField(max_length=255)
    registration_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        default="",
    )
    physical_address = models.TextField(blank=True, default="")
    county = models.CharField(max_length=100, blank=True, default="")
    contact_person = models.CharField(max_length=255, blank=True, default="")
    contact_designation = models.CharField(max_length=255, blank=True, default="")
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.ACTIVE,
    )

    # Location / Transport
    town = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Town or locality of the school.",
    )
    gps_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    gps_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    transport_zone = models.ForeignKey(
        "equipment.TransportZone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="school_profiles",
        help_text="The transport zone used to calculate delivery fees.",
    )

    # Liability / Trust
    liability_status = models.CharField(
        max_length=20,
        choices=LiabilityStatus.choices,
        default=LiabilityStatus.CLEAR,
        help_text="Blocks new bookings if HAS_OUTSTANDING.",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "School Profile"
        verbose_name_plural = "School Profiles"

    def __str__(self):
        return f"{self.school_name} ({self.user.email})"

    def deactivate(self):
        self.account_status = AccountStatus.BLOCKED
        self.save(update_fields=["account_status", "updated_at"])
