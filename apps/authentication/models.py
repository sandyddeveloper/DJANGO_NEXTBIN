from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.authentication.crypto_utils import (
    EncryptedTextField,
    hash_value,
    mask_email,
    mask_mobile,
    mask_password,
    mask_pin,
)
from apps.constants.authConstant import OtpPurpose, RoleChoices


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("role", RoleChoices.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    profile_code = models.CharField(primary_key=True, max_length=20, editable=False)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)

    # Encrypted, hashed, and masked fields
    email = EncryptedTextField(default="")
    email_hashed = models.CharField(unique=True, max_length=64, db_index=True, default="")
    email_masked = models.CharField(max_length=255, default="")

    mobile = EncryptedTextField(blank=True, null=True)
    mobile_hashed = models.CharField(
        unique=True, max_length=64, blank=True, null=True, db_index=True
    )
    mobile_masked = models.CharField(max_length=255, blank=True, null=True)

    profile_image = models.ImageField(upload_to="profile_images/", blank=True, null=True)

    password = EncryptedTextField(default="")
    password_hashed = models.CharField(max_length=128, default="")
    password_masked = models.CharField(max_length=255, default="")

    pin = EncryptedTextField(blank=True, null=True)
    pin_hashed = models.CharField(max_length=128, blank=True, null=True)
    pin_masked = models.CharField(max_length=255, blank=True, null=True)

    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.USER)
    assigned_role = models.ForeignKey(
        "custom_admin.Role",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email_hashed"
    REQUIRED_FIELDS = ["first_name", "email"]

    def save(self, *args, **kwargs):
        # Auto-compute hashed and masked fields on save
        if self.email:
            self.email_hashed = hash_value(self.email)
            self.email_masked = mask_email(self.email)

        if self.mobile:
            self.mobile_hashed = hash_value(self.mobile)
            self.mobile_masked = mask_mobile(self.mobile)
        else:
            self.mobile_hashed = None
            self.mobile_masked = None

        if self.password:
            self.password_hashed = hash_value(self.password)
            self.password_masked = mask_password(self.password)

        if self.pin:
            self.pin_hashed = hash_value(self.pin)
            self.pin_masked = mask_pin(self.pin)
        else:
            self.pin_hashed = None
            self.pin_masked = None

        if not self.profile_code:
            prefix = "NBS" if self.role == RoleChoices.SUPER_ADMIN else "NBU"
            last_user = (
                CustomUser.objects.filter(profile_code__startswith=prefix)
                .order_by("-profile_code")
                .first()
            )
            if not last_user:
                self.profile_code = f"{prefix}00001"
            else:
                import re

                match = re.search(r"\d+", last_user.profile_code)
                if match:
                    num = int(match.group())
                    self.profile_code = f"{prefix}{(num + 1):05d}"
                else:
                    self.profile_code = f"{prefix}00001"
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = raw_password
        self._password = raw_password

    def check_password(self, raw_password):
        if not self.password:
            return False
        return raw_password == self.password

    def set_pin(self, raw_pin):
        self.pin = raw_pin

    def check_pin(self, raw_pin):
        if not self.pin:
            return False
        return raw_pin == self.pin

    def __str__(self):
        return f"{self.email} ({self.profile_code})"


class EmailOTP(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20, choices=OtpPurpose.choices, default=OtpPurpose.VERIFICATION
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.email} ({self.otp})"
