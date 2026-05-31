from datetime import timedelta
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from django.contrib.auth import get_user_model

from django.conf import settings
from apps.authentication.models import EmailOTP
from apps.constants.authConstant import OtpPurpose, RoleChoices
from apps.authentication.crypto_utils import hash_value
from .serializers import (
    SignupSerializer,
    OTPVerifySerializer,
    LoginSerializer,
    TokenRefreshSerializer,
    UserProfileSerializer,
    ResendOTPSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ForgotPinSerializer,
    ResetPinSerializer,
    SuperAdminUserCreateSerializer,
    UserProfileUpdateSerializer,
)
from apps.authentication.utils import generate_otp, send_otp_email, generate_tokens

User = get_user_model()


@extend_schema(tags=['Signup'])
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
                        value={"message": "Verification OTP sent to santhoshrajk1812@gmail.com. Please verify to activate account."}
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation error.")
        }
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
                expires_at=expiry_time
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
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response(
                {"message": f"Verification OTP sent to {user.email}. Please verify to activate account."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Signup'])
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
                            "email": "santhoshrajk1812@gmail.com"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid or expired OTP.")
        }
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            otp_record = serializer.validated_data['otp_record']
            email = serializer.validated_data['email']
            
            # Activate user
            try:
                user = User.objects.get(email_hashed=hash_value(email))
                user.is_verified = True
                user.is_active = True
                user.save()  # Generates profile_code in custom save() method
                
                # Cleanup OTP record
                otp_record.delete()
                
                return Response({
                    "message": "Account verified successfully.",
                    "profile_code": user.profile_code,
                    "email": user.email
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({"error": "User matching verification email does not exist."}, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Login'])
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
                            "active_profile_code": "NBU00001"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Incorrect credentials or unverified account.")
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT Access/Refresh pair
            access_token, refresh_token = generate_tokens(user)
            
            return Response({
                "access": access_token,
                "refresh": refresh_token,
                "active_role": user.role,
                "active_profile_code": user.profile_code
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Login'])
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
                            "active_profile_code": "NBU00001"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid or expired refresh token.")
        }
    )
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate new access/refresh tokens
            access_token, _ = generate_tokens(user)
            
            return Response({
                "access": access_token,
                "active_role": user.role,
                "active_profile_code": user.profile_code
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Login'])
class UserProfileView(APIView):
    """
    Retrieve profile details for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve user profile",
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="Unauthorized — valid access token required.")
        }
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=['Signup'])
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
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Generate OTP
            otp_code = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=5)
            
            # Save OTP record
            EmailOTP.objects.filter(email=email).delete()
            EmailOTP.objects.create(
                email=email,
                otp=otp_code,
                purpose=OtpPurpose.VERIFICATION,
                expires_at=expiry_time
            )
            
            # Send Email
            try:
                send_otp_email(email, otp_code)
            except Exception as e:
                EmailOTP.objects.filter(email=email).delete()
                return Response(
                    {"error": f"Failed to send email verification OTP: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response(
                {"message": f"Verification OTP resent to {email}."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Login'])
class ForgotPasswordView(APIView):
    """
    Forgot Password - request email OTP.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request password reset OTP",
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset OTP sent to email."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            email = user.email
            
            # Generate OTP
            otp_code = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=5)
            
            # Save OTP record
            EmailOTP.objects.filter(email=email).delete()
            EmailOTP.objects.create(
                email=email,
                otp=otp_code,
                purpose=OtpPurpose.PASSWORD_RESET,
                expires_at=expiry_time
            )
            
            # Send Email
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject="Nextbin Password Reset OTP",
                    message=f"Your OTP for resetting password is: {otp_code}. It will expire in 5 minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                EmailOTP.objects.filter(email=email).delete()
                return Response(
                    {"error": f"Failed to send password reset OTP email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response(
                {"message": f"Password reset OTP sent to {email}."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Login'])
class ResetPasswordView(APIView):
    """
    Reset Password using OTP.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Reset password using OTP",
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp_record = serializer.validated_data['otp_record']
            new_password = serializer.validated_data['new_password']
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Cleanup OTP
            otp_record.delete()
            
            return Response(
                {"message": "Password reset successfully. You can now login with your new password."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Login'])
class ForgotPinView(APIView):
    """
    Forgot PIN - request email OTP.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request PIN reset OTP",
        request=ForgotPinSerializer,
        responses={
            200: OpenApiResponse(description="PIN reset OTP sent to email."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = ForgotPinSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            email = user.email
            
            # Generate OTP
            otp_code = generate_otp()
            expiry_time = timezone.now() + timedelta(minutes=5)
            
            # Save OTP record
            EmailOTP.objects.filter(email=email).delete()
            EmailOTP.objects.create(
                email=email,
                otp=otp_code,
                purpose=OtpPurpose.PIN_RESET,
                expires_at=expiry_time
            )
            
            # Send Email
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject="Nextbin PIN Reset OTP",
                    message=f"Your OTP for resetting PIN is: {otp_code}. It will expire in 5 minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                EmailOTP.objects.filter(email=email).delete()
                return Response(
                    {"error": f"Failed to send PIN reset OTP email: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            return Response(
                {"message": f"PIN reset OTP sent to {email}."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Login'])
class ResetPinView(APIView):
    """
    Reset PIN using OTP.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Reset PIN using OTP",
        request=ResetPinSerializer,
        responses={
            200: OpenApiResponse(description="PIN reset successfully."),
            400: OpenApiResponse(description="Validation error.")
        }
    )
    def post(self, request):
        serializer = ResetPinSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp_record = serializer.validated_data['otp_record']
            new_pin = serializer.validated_data['new_pin']
            
            # Set new PIN
            user.set_pin(new_pin)
            user.save()
            
            # Cleanup OTP
            otp_record.delete()
            
            return Response(
                {"message": "PIN reset successfully. You can now login with your new PIN."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IsSuperAdminOrOwner(BasePermission):
    """
    Custom permission to only allow Super Admins or the profile owner.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.role == RoleChoices.SUPER_ADMIN or request.user.profile_code == obj.profile_code


@extend_schema(tags=['User Profile'])
class UserProfileViewSet(viewsets.ModelViewSet):
    """
    Profile CRUD for users.
    * GET /api/v1/user/profiles/ - List all users (Super Admin only)
    * POST /api/v1/user/profiles/ - Direct create user (Super Admin only)
    * GET /api/v1/user/profiles/{profile_code}/ - Retrieve user details (Super Admin or Profile Owner)
    * PUT/PATCH /api/v1/user/profiles/{profile_code}/ - Update user profile (Super Admin or Profile Owner)
    * DELETE /api/v1/user/profiles/{profile_code}/ - Deactivate user profile (Super Admin or Profile Owner)
    """
    queryset = User.objects.all().order_by('profile_code')
    permission_classes = [IsAuthenticated, IsSuperAdminOrOwner]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'create':
            return SuperAdminUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def get_queryset(self):
        return User.objects.all().order_by('profile_code')

    def list(self, request, *args, **kwargs):
        # Explicit check for Super Admin role on list
        if request.user.role != RoleChoices.SUPER_ADMIN:
            raise PermissionDenied("You do not have permission to view the list of users.")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # Explicit check for Super Admin role on create
        if request.user.role != RoleChoices.SUPER_ADMIN:
            raise PermissionDenied("You do not have permission to create users directly.")
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete / Deactivate user profile.
        """
        obj = self.get_object()
        # Soft delete logic
        obj.is_active = False
        obj.save()
        
        return Response(
            {"message": f"Profile {obj.profile_code} deactivated successfully."},
            status=status.HTTP_200_OK
        )
