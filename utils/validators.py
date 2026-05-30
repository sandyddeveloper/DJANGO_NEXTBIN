"""
Custom validators for the application.
"""

from django.core.exceptions import ValidationError
import re


def validate_phone_number(value):
    """Validate phone number format."""
    pattern = r'^\+?1?\d{9,15}$'
    if not re.match(pattern, value.replace(' ', '').replace('-', '')):
        raise ValidationError('Invalid phone number format.')


def validate_username(value):
    """Validate username format."""
    if len(value) < 3:
        raise ValidationError('Username must be at least 3 characters long.')
    if not re.match(r'^[a-zA-Z0-9_-]*$', value):
        raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')


def validate_url(value):
    """Validate URL format."""
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&/=]*)$'
    if not re.match(pattern, value):
        raise ValidationError('Invalid URL format.')
