import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import EmailOTP
from apps.constants.authConstant import OtpPurpose, RoleChoices

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def verified_user(db):
    """Create and return a verified CustomUser."""
    user = User.objects.create_user(
        email="johndoe@example.com",
        password="oldpassword123",
        first_name="John",
        role=RoleChoices.USER,
    )
    user.set_pin("111111")
    user.is_verified = True
    user.is_active = True
    user.save()
    return user


@pytest.mark.django_db
def test_forgot_password_success(api_client, verified_user):
    url = reverse("v1:forgot-password")
    response = api_client.post(
        url, {"profile_code": verified_user.profile_code}, format="json", secure=True
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Password reset OTP sent" in response.data["message"]

    # Check that OTP record was created in DB
    otp_record = EmailOTP.objects.get(email=verified_user.email, purpose=OtpPurpose.PASSWORD_RESET)
    assert otp_record is not None
    assert len(otp_record.otp) == 6


@pytest.mark.django_db
def test_forgot_password_invalid_profile_code(api_client):
    url = reverse("v1:forgot-password")
    response = api_client.post(url, {"profile_code": "NBU99999"}, format="json", secure=True)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "profile_code" in response.data


@pytest.mark.django_db
def test_reset_password_success(api_client, verified_user):
    # First request forgot password to generate OTP
    url_forgot = reverse("v1:forgot-password")
    api_client.post(
        url_forgot, {"profile_code": verified_user.profile_code}, format="json", secure=True
    )

    otp_record = EmailOTP.objects.get(email=verified_user.email, purpose=OtpPurpose.PASSWORD_RESET)

    # Now reset password
    url_reset = reverse("v1:reset-password")
    response = api_client.post(
        url_reset,
        {
            "profile_code": verified_user.profile_code,
            "otp": otp_record.otp,
            "new_password": "newpassword123",
        },
        format="json",
        secure=True,
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify password was updated in DB
    verified_user.refresh_from_db()
    assert verified_user.check_password("newpassword123")

    # Verify OTP record was deleted
    otp_exists = EmailOTP.objects.filter(
        email=verified_user.email, purpose=OtpPurpose.PASSWORD_RESET
    ).exists()
    assert not otp_exists


@pytest.mark.django_db
def test_reset_password_invalid_otp(api_client, verified_user):
    url_reset = reverse("v1:reset-password")
    response = api_client.post(
        url_reset,
        {
            "profile_code": verified_user.profile_code,
            "otp": "000000",
            "new_password": "newpassword123",
        },
        format="json",
        secure=True,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_forgot_pin_success(api_client, verified_user):
    url = reverse("v1:forgot-pin")
    response = api_client.post(
        url, {"profile_code": verified_user.profile_code}, format="json", secure=True
    )

    assert response.status_code == status.HTTP_200_OK
    assert "PIN reset OTP sent" in response.data["message"]

    # Check that OTP record was created in DB
    otp_record = EmailOTP.objects.get(email=verified_user.email, purpose=OtpPurpose.PIN_RESET)
    assert otp_record is not None


@pytest.mark.django_db
def test_reset_pin_success(api_client, verified_user):
    # First request forgot PIN to generate OTP
    url_forgot = reverse("v1:forgot-pin")
    api_client.post(
        url_forgot, {"profile_code": verified_user.profile_code}, format="json", secure=True
    )

    otp_record = EmailOTP.objects.get(email=verified_user.email, purpose=OtpPurpose.PIN_RESET)

    # Now reset PIN
    url_reset = reverse("v1:reset-pin")
    response = api_client.post(
        url_reset,
        {"profile_code": verified_user.profile_code, "otp": otp_record.otp, "new_pin": "222222"},
        format="json",
        secure=True,
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify PIN was updated in DB
    verified_user.refresh_from_db()
    assert verified_user.check_pin("222222")

    # Verify OTP record was deleted
    otp_exists = EmailOTP.objects.filter(
        email=verified_user.email, purpose=OtpPurpose.PIN_RESET
    ).exists()
    assert not otp_exists
