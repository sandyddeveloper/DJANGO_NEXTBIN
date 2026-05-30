import datetime
import random

import jwt
from django.conf import settings
from django.core.mail import send_mail


def generate_tokens(user):
    """
    Generates a secure access and refresh JWT token pair for the user.
    Claims are customized with user roles and profile codes.
    """
    now = datetime.datetime.utcnow()

    # 1 hour expiration for access token
    access_expiry = now + datetime.timedelta(hours=1)
    # 7 days expiration for refresh token
    refresh_expiry = now + datetime.timedelta(days=7)

    access_payload = {
        "user_id": user.profile_code,
        "email": user.email,
        "active_role": user.role,
        "active_profile_code": user.profile_code,
        "exp": access_expiry,
        "iat": now,
        "token_type": "access",
    }

    refresh_payload = {
        "user_id": user.profile_code,
        "exp": refresh_expiry,
        "iat": now,
        "token_type": "refresh",
    }

    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm="HS256")

    # Ensure standard string format
    if isinstance(access_token, bytes):
        access_token = access_token.decode("utf-8")
    if isinstance(refresh_token, bytes):
        refresh_token = refresh_token.decode("utf-8")

    return access_token, refresh_token


def decode_token(token):
    """
    Decodes and validates the signature and expiration of a JWT token.
    Returns the decoded payload if valid, otherwise raises exception.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return payload


def generate_otp():
    """Generates a secure 6-digit verification code."""
    return f"{random.randint(100000, 999999)}"


def send_otp_email(email, otp):
    """
    Sends the email verification OTP to the target email address.
    Uses Django's send_mail function with standard SMTP.
    """
    subject = "Nextbin Account Verification OTP"
    message = (
        f"Hello,\n\n"
        f"Thank you for signing up for Nextbin.\n"
        f"Your 6-digit email verification OTP is: {otp}\n\n"
        f"This code will expire in 5 minutes.\n\n"
        f"If you did not initiate this request, please ignore this email.\n\n"
        f"Best regards,\n"
        f"Nextbin Security Team"
    )

    # Send email using config settings
    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
