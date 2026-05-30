import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()


class SafeJWTAuthentication(BaseAuthentication):
    """
    Custom DRF Authentication class using PyJWT.
    Checks the incoming Authorization header for a 'Bearer <token>' pattern.
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]
        try:
            # Decode the access token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        # Ensure this is an access token, not a refresh token
        if payload.get('token_type') != 'access':
            raise AuthenticationFailed('Invalid token type')

        profile_code = payload.get('active_profile_code')
        if not profile_code:
            raise AuthenticationFailed('Token missing profile code claim')

        try:
            # Query by profile_code (which is primary key)
            user = User.objects.get(profile_code=profile_code)
        except User.DoesNotExist:
            raise AuthenticationFailed('User matching token profile code not found')

        if not user.is_active:
            raise AuthenticationFailed('User account is deactivated')

        if not user.is_verified:
            raise AuthenticationFailed('User account email is not verified')

        return (user, token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'


# DRF-Spectacular extension for Swagger UI / OpenAPI schema documentation
try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class SafeJWTAuthenticationScheme(OpenApiAuthenticationExtension):
        target_class = 'apps.authentication.auth.SafeJWTAuthentication'
        name = 'SafeJWTAuthentication'

        def get_security_definition(self, auto_schema):
            return {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Custom JWT Authentication using active_profile_code payload claim.'
            }
except ImportError:
    pass

