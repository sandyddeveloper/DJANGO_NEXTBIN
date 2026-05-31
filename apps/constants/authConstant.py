from django.db import models


class RoleChoices(models.TextChoices):
    USER = "USER", "User"
    STAFF = "STAFF", "Staff"
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"


class OtpPurpose(models.TextChoices):
    VERIFICATION = "verification", "Email Verification"
    PASSWORD_RESET = "password_reset", "Password Reset"
    PIN_RESET = "pin_reset", "PIN Reset"
