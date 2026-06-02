from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.crypto_utils import hash_value
from apps.authentication.models import EmailOTP
from apps.authentication.utils import generate_otp, generate_tokens, send_otp_email
from apps.constants.authConstant import OtpPurpose, RoleChoices
from apps.core.permissions import CoreSystemRoles, HasActivePermission, UserPerms

from .serializers import (
    ForgotPasswordSerializer,
    ForgotPinSerializer,
    LoginSerializer,
    OTPVerifySerializer,
    ResendOTPSerializer,
    ResetPasswordSerializer,
    ResetPinSerializer,
    SignupSerializer,
    SuperAdminUserCreateSerializer,
    TokenRefreshSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)

User = get_user_model()


@extend_schema(tags=["Signup"])
class SignupView(APIView):
    """
    User registration endpoint.
    Creates an inactive user and triggers email verification by sending a 6-digit OTP.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register a new user",
        request=SignupSerializer,
        responses={
            201: OpenApiResponse(
                description="Registration initiated. OTP sent to email.",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "message": (
                                "Verification OTP sent to santhoshrajk1812@gmail.com. "
                                "Please verify to activate account."
                            )
                        },
                    )
                ],
            ),
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate OTP
            otp_code = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=5)

            # Save OTP record (overwrite existing OTPs for the same email if they exist)
            EmailOTP.objects.filter(email=user.email).delete()
            EmailOTP.objects.create(
                email=user.email,
                otp=otp_code,
                purpose=OtpPurpose.VERIFICATION,
                expires_at=expiry_time,
            )

            # Send Email
            try:
                send_otp_email(user.email, otp_code)
            except Exception as e:
                # If email fails, delete user to allow retry and return error
                user.delete()
                EmailOTP.objects.filter(email=user.email).delete()
                return Response(
                    {"error": f"Failed to send email verification OTP: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "message": (
                        f"Verification OTP sent to {user.email}. "
                        "Please verify to activate account."
                    )
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Signup"])
class VerifyOTPView(APIView):
    """
    Email verification endpoint.
    Submitting the correct OTP activates the user profile and generates their unique profile code.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify email OTP",
        request=OTPVerifySerializer,
        responses={
            200: OpenApiResponse(
                description="Account verified successfully.",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "message": "Account verified successfully.",
                            "profile_code": "NBU00001",
                            "email": "santhoshrajk1812@gmail.com",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(description="Invalid or expired OTP."),
        },
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            otp_record = serializer.validated_data["otp_record"]
            email = serializer.validated_data["email"]

            # Activate user
            try:
                user = User.objects.get(email_hashed=hash_value(email))
                user.is_verified = True
                user.is_active = True
                user.save()  # Generates profile_code in custom save() method

                # Cleanup OTP record
                otp_record.delete()

                return Response(
                    {
                        "message": "Account verified successfully.",
                        "profile_code": user.profile_code,
                        "email": user.email,
                    },
                    status=status.HTTP_200_OK,
                )

            except User.DoesNotExist:
                return Response(
                    {"error": "User matching verification email does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Login"])
class LoginView(APIView):
    """
    User login endpoint.
    Supports email/phone logging in with either password or PIN. Returns access and refresh JWTs.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Authenticate user and login",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Authentication successful.",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "active_role": "USER",
                            "active_profile_code": "NBU00001",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(description="Incorrect credentials or unverified account."),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Generate JWT Access/Refresh pair
            access_token, refresh_token = generate_tokens(user)

            return Response(
                {
                    "access": access_token,
                    "refresh": refresh_token,
                    "active_role": user.role,
                    "active_profile_code": user.profile_code,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Login"])
class TokenRefreshView(APIView):
    """
    Obtain a new access token using a valid refresh token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Refresh access token",
        request=TokenRefreshSerializer,
        responses={
            200: OpenApiResponse(
                description="Token refreshed.",
                examples=[
                    OpenApiExample(
                        "Success response",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "active_role": "USER",
                            "active_profile_code": "NBU00001",
                        },
                    )
                ],
            ),
            400: OpenApiResponse(description="Invalid or expired refresh token."),
        },
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Generate new access/refresh tokens
            access_token, _ = generate_tokens(user)

            return Response(
                {
                    "access": access_token,
                    "active_role": user.role,
                    "active_profile_code": user.profile_code,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Login"])
class UserProfileView(APIView):
    """
    Retrieve profile details for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve user profile",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Unauthorized — valid access token required."),
        },
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Signup"])
class ResendOTPView(APIView):
    """
    Resend signup verification OTP.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Resend verification OTP",
        request=ResendOTPSerializer,
        responses={
            200: OpenApiResponse(description="Verification OTP sent to email."),
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # Generate OTP
            otp_code = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=5)

            # Save OTP record
            EmailOTP.objects.filter(email=email).delete()
            EmailOTP.objects.create(
                email=email, otp=otp_code, purpose=OtpPurpose.VERIFICATION, expires_at=expiry_time
            )

            # Send Email
            try:
                send_otp_email(email, otp_code)
            except Exception as e:
                EmailOTP.objects.filter(email=email).delete()
                return Response(
                    {"error": f"Failed to send email verification OTP: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {"message": f"Verification OTP resent to {email}."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Login"])
class ForgotPasswordOrPinView(APIView):
    """
    Request OTP for resetting password or PIN.
    """

    permission_classes = [AllowAny]
    credential_type = None  # "password" or "pin", to be set via as_view()

    def get_serializer_class(self):
        if self.credential_type == "pin":
            return ForgotPinSerializer
        return ForgotPasswordSerializer

    @property
    def serializer_class(self):
        return self.get_serializer_class()

    @extend_schema(
        summary="Request credential reset OTP",
        responses={
            200: OpenApiResponse(description="Reset OTP sent to email."),
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def post(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            email = user.email

            # Generate OTP
            otp_code = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=5)

            purpose = OtpPurpose.PIN_RESET if self.credential_type == "pin" else OtpPurpose.PASSWORD_RESET
            subject_label = "PIN" if self.credential_type == "pin" else "Password"

            # Save OTP record
            EmailOTP.objects.filter(email=email).delete()
            EmailOTP.objects.create(
                email=email, otp=otp_code, purpose=purpose, expires_at=expiry_time
            )

            # Send Email
            try:
                from django.core.mail import send_mail

                send_mail(
                    subject=f"Nextbin {subject_label} Reset OTP",
                    message=(
                        f"Your OTP for resetting {subject_label.lower()} is: {otp_code}. "
                        "It will expire in 5 minutes."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                EmailOTP.objects.filter(email=email).delete()
                return Response(
                    {"error": f"Failed to send {subject_label.lower()} reset OTP email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {"message": f"{subject_label} reset OTP sent to {email}."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Login"])
class ResetPasswordOrPinView(APIView):
    """
    Reset Password or PIN using OTP.
    """

    permission_classes = [AllowAny]
    credential_type = None  # "password" or "pin", to be set via as_view()

    def get_serializer_class(self):
        if self.credential_type == "pin":
            return ResetPinSerializer
        return ResetPasswordSerializer

    @property
    def serializer_class(self):
        return self.get_serializer_class()

    @extend_schema(
        summary="Reset credential using OTP",
        responses={
            200: OpenApiResponse(description="Credential reset successfully."),
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def post(self, request):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            otp_record = serializer.validated_data["otp_record"]

            if self.credential_type == "pin":
                new_pin = serializer.validated_data["new_pin"]
                user.set_pin(new_pin)
                message = "PIN reset successfully. You can now login with your new PIN."
            else:
                new_password = serializer.validated_data["new_password"]
                user.set_password(new_password)
                message = "Password reset successfully. You can now login with your new password."

            user.save()

            # Cleanup OTP
            otp_record.delete()

            return Response(
                {"message": message},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IsSuperAdminOrOwner(BasePermission):
    """
    Custom permission to only allow Super Admins, Admins, or the profile owner.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.user.role in (
                CoreSystemRoles.SUPER_ADMIN,
                CoreSystemRoles.ADMIN,
            )
            or request.user.profile_code == obj.profile_code
        )


class UserProfileListView(APIView):
    """
    Profile List and Create for users.
    * GET /api/v1/user/profiles/ - List all users (Super Admin only)
    * POST /api/v1/user/profiles/ - Direct create user (Super Admin only)
    """
    permission_classes = [IsAuthenticated, HasActivePermission(UserPerms.VIEW_USERS)]
    serializer_class = UserProfileSerializer

    @extend_schema(
        operation_id="user_profiles_list",
        summary="List all users",
        responses={200: UserProfileSerializer(many=True)},
        tags=["User Profile"]
    )
    def get(self, request, *args, **kwargs):
        queryset = User.objects.all().order_by("profile_code")
        serializer = UserProfileSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="user_profiles_create",
        summary="Direct create user",
        request=SuperAdminUserCreateSerializer,
        responses={201: UserProfileSerializer},
        tags=["User Profile"]
    )
    def post(self, request, *args, **kwargs):
        serializer = SuperAdminUserCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserProfileSerializer(user, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileDetailView(APIView):
    """
    Profile Detail, Update, and Deactivate for users.
    * GET /api/v1/user/profiles/{profile_code}/ - Retrieve user details (Super Admin or Profile Owner)
    * PUT/PATCH /api/v1/user/profiles/{profile_code}/ - Update user profile (Super Admin or Profile Owner)
    * DELETE /api/v1/user/profiles/{profile_code}/ - Deactivate user profile (Super Admin or Profile Owner)
    """
    permission_classes = [IsAuthenticated, IsSuperAdminOrOwner]
    serializer_class = UserProfileSerializer

    def get_object(self, pk):
        try:
            obj = User.objects.get(pk=pk)
            self.check_object_permissions(self.request, obj)
            return obj
        except User.DoesNotExist:
            return None

    @extend_schema(
        operation_id="user_profiles_retrieve",
        summary="Retrieve user profile details",
        responses={200: UserProfileSerializer},
        tags=["User Profile"]
    )
    def get(self, request, pk, *args, **kwargs):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileSerializer(obj, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)



    @extend_schema(
        operation_id="user_profiles_partial_update",
        summary="Update user profile details (partial update)",
        request=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer},
        tags=["User Profile"]
    )
    def patch(self, request, pk, *args, **kwargs):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileUpdateSerializer(obj, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserProfileSerializer(user, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="user_profiles_destroy",
        summary="Soft delete/deactivate user profile",
        responses={200: OpenApiResponse(description="Profile deactivated successfully.")},
        tags=["User Profile"]
    )
    def delete(self, request, pk, *args, **kwargs):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_active = False
        obj.save()
        return Response(
            {"message": f"Profile {obj.profile_code} deactivated successfully."},
            status=status.HTTP_200_OK,
        )






