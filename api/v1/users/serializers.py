import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.authentication.crypto_utils import hash_value
from apps.authentication.models import EmailOTP
from apps.constants.authConstant import OtpPurpose, RoleChoices

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """Serializer for registering a new user."""

    password = serializers.CharField(write_only=True, min_length=8)
    pin = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "mobile",
            "profile_image",
            "password",
            "pin",
            "role",
        ]
        extra_kwargs = {
            "middle_name": {"required": False},
            "last_name": {"required": False},
            "mobile": {"required": False},
            "profile_image": {"required": False},
            "role": {"required": False},
        }

    def validate_email(self, value):
        if User.objects.filter(email_hashed=hash_value(value)).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_mobile(self, value):
        if value and User.objects.filter(mobile_hashed=hash_value(value)).exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")
        return value

    def validate_pin(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("PIN must be a 6-digit numeric code.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        pin = validated_data.pop("pin")

        user = User(**validated_data)
        user.set_password(password)
        user.set_pin(pin)

        # User starts out as unverified until email OTP confirmation
        user.is_verified = False
        user.is_active = False
        user.save()
        return user


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for verifying the email OTP."""

    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            otp_record = EmailOTP.objects.get(email=email, otp=otp, purpose=OtpPurpose.VERIFICATION)
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP or email address.")

        if otp_record.is_expired():
            otp_record.delete()
            raise serializers.ValidationError("This OTP has expired. Please request a new one.")

        attrs["otp_record"] = otp_record
        return attrs


class LoginSerializer(serializers.Serializer):
    """Serializer for logging in with either password or PIN."""

    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    pin = serializers.CharField(required=False, write_only=True, min_length=6, max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        mobile = attrs.get("mobile")
        password = attrs.get("password")
        pin = attrs.get("pin")

        # Check identification (email or mobile)
        if not email and not mobile:
            raise serializers.ValidationError("You must provide either email or mobile.")

        # Check authentication method (password or pin)
        if not password and not pin:
            raise serializers.ValidationError("You must provide either password or pin.")

        # Find user
        user = None
        if email:
            try:
                user = User.objects.get(email_hashed=hash_value(email))
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this email not found.")
        elif mobile:
            try:
                user = User.objects.get(mobile_hashed=hash_value(mobile))
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this mobile number not found.")

        # Validate verified and active status
        if user and not user.is_verified:
            raise serializers.ValidationError(
                "Account email is not verified. Please verify your email first."
            )
        if user and not user.is_active:
            raise serializers.ValidationError("Account is deactivated.")

        # Authenticate
        if password:
            if not user.check_password(password):
                raise serializers.ValidationError("Incorrect password.")
        elif pin:
            if not user.check_pin(pin):
                raise serializers.ValidationError("Incorrect PIN.")

        attrs["user"] = user
        return attrs


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for obtaining a new access token from a refresh token."""

    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh_token = attrs.get("refresh")
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise serializers.ValidationError("Refresh token has expired.")
        except jwt.InvalidTokenError:
            raise serializers.ValidationError("Invalid refresh token.")

        if payload.get("token_type") != "refresh":
            raise serializers.ValidationError("Invalid token type. Refresh token required.")

        user_id = payload.get("user_id")
        try:
            user = User.objects.get(profile_code=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User matching token not found.")

        if not user.is_active:
            raise serializers.ValidationError("User account is deactivated.")

        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving user details."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "profile_code",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "email_masked",
            "email_hashed",
            "mobile",
            "mobile_masked",
            "mobile_hashed",
            "profile_image",
            "role",
            "role_display",
            "is_verified",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending the verification OTP."""

    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email_hashed=hash_value(value))
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        if user.is_verified:
            raise serializers.ValidationError("User is already verified.")

        return value


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for requesting a password reset OTP."""

    profile_code = serializers.CharField()

    def validate(self, attrs):
        profile_code = attrs.get("profile_code")
        try:
            user = User.objects.get(profile_code=profile_code)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"profile_code": "User with this profile code does not exist."}
            )

        if not user.is_verified:
            raise serializers.ValidationError({"profile_code": "User email is not verified yet."})

        attrs["user"] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password with an OTP."""

    profile_code = serializers.CharField()
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        profile_code = attrs.get("profile_code")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(profile_code=profile_code)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"profile_code": "User with this profile code does not exist."}
            )

        if not user.is_verified:
            raise serializers.ValidationError({"profile_code": "User email is not verified yet."})

        email = user.email

        try:
            otp_record = EmailOTP.objects.get(
                email=email, otp=otp, purpose=OtpPurpose.PASSWORD_RESET
            )
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP or profile code.")

        if otp_record.is_expired():
            otp_record.delete()
            raise serializers.ValidationError("This OTP has expired. Please request a new one.")

        attrs["user"] = user
        attrs["otp_record"] = otp_record
        return attrs


class ForgotPinSerializer(serializers.Serializer):
    """Serializer for requesting a PIN reset OTP."""

    profile_code = serializers.CharField()

    def validate(self, attrs):
        profile_code = attrs.get("profile_code")
        try:
            user = User.objects.get(profile_code=profile_code)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"profile_code": "User with this profile code does not exist."}
            )

        if not user.is_verified:
            raise serializers.ValidationError({"profile_code": "User email is not verified yet."})

        attrs["user"] = user
        return attrs


class ResetPinSerializer(serializers.Serializer):
    """Serializer for resetting PIN with an OTP."""

    profile_code = serializers.CharField()
    otp = serializers.CharField(min_length=6, max_length=6)
    new_pin = serializers.CharField(write_only=True, min_length=6, max_length=6)

    def validate_new_pin(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("PIN must be a 6-digit numeric code.")
        return value

    def validate(self, attrs):
        profile_code = attrs.get("profile_code")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(profile_code=profile_code)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"profile_code": "User with this profile code does not exist."}
            )

        if not user.is_verified:
            raise serializers.ValidationError({"profile_code": "User email is not verified yet."})

        email = user.email

        try:
            otp_record = EmailOTP.objects.get(email=email, otp=otp, purpose=OtpPurpose.PIN_RESET)
        except EmailOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP or profile code.")

        if otp_record.is_expired():
            otp_record.delete()
            raise serializers.ValidationError("This OTP has expired. Please request a new one.")

        attrs["user"] = user
        attrs["otp_record"] = otp_record
        return attrs


class SuperAdminUserCreateSerializer(serializers.ModelSerializer):
    """Serializer used by Super Admin to directly create a verified and active user."""

    password = serializers.CharField(write_only=True, min_length=8)
    pin = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = [
            "profile_code",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "mobile",
            "profile_image",
            "password",
            "pin",
            "role",
        ]
        read_only_fields = ["profile_code"]
        extra_kwargs = {
            "middle_name": {"required": False},
            "last_name": {"required": False},
            "mobile": {"required": False},
            "profile_image": {"required": False},
            "role": {"required": False},
        }

    def validate_email(self, value):
        if User.objects.filter(email_hashed=hash_value(value)).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_mobile(self, value):
        if value and User.objects.filter(mobile_hashed=hash_value(value)).exists():
            raise serializers.ValidationError("A user with this mobile number already exists.")
        return value

    def validate_pin(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("PIN must be a 6-digit numeric code.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        pin = validated_data.pop("pin")

        user = User(**validated_data)
        user.set_password(password)
        user.set_pin(pin)

        # Super Admin created users are immediately verified and active
        user.is_verified = True
        user.is_active = True
        user.save()
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile fields."""

    class Meta:
        model = User
        fields = ["first_name", "middle_name", "last_name", "mobile", "profile_image", "role"]
        extra_kwargs = {
            "first_name": {"required": False},
            "middle_name": {"required": False},
            "last_name": {"required": False},
            "mobile": {"required": False},
            "profile_image": {"required": False},
            "role": {"required": False},
        }

    def validate_mobile(self, value):
        if value:
            # Check if this mobile is already taken by another user
            user = self.instance
            qs = User.objects.filter(mobile_hashed=hash_value(value))
            if user:
                qs = qs.exclude(profile_code=user.profile_code)
            if qs.exists():
                raise serializers.ValidationError("A user with this mobile number already exists.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user:
            # If the user is not a SUPER_ADMIN and they are attempting
            # to change their role, block it
            if "role" in attrs and request.user.role != RoleChoices.SUPER_ADMIN:
                raise serializers.ValidationError(
                    {"role": "You do not have permission to modify user roles."}
                )
        return attrs
