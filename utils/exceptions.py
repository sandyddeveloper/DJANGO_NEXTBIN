"""
Custom exceptions for the application.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class APIError(APIException):
    """Base API exception."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred'


class NotFoundError(APIException):
    """Resource not found."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found'


class UnauthorizedError(APIException):
    """Unauthorized access."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Unauthorized'


class ForbiddenError(APIException):
    """Forbidden access."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Forbidden'


class ValidationError(APIException):
    """Validation error."""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Validation error'


class ConflictError(APIException):
    """Resource conflict."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Resource conflict'


class RateLimitError(APIException):
    """Rate limit exceeded."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded'


class InternalError(APIException):
    """Internal server error."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Internal server error'
