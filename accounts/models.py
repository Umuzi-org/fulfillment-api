from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    STANDARD = "STANDARD", "Standard"


class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An account must have an email address.")
        email = self.normalize_email(email).lower()
        account = self.model(email=email, **extra_fields)
        account.set_password(password)
        account.save(using=self._db)
        return account

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("role") != Role.ADMIN:
            raise ValueError("A superuser must have role ADMIN.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Account(AbstractBaseUser, PermissionsMixin):
    """Person who can sign in and own fulfillment orders."""

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.STANDARD,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email
