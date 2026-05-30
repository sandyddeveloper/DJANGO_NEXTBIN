"""
Core app — models for API logs, user activity logs, system logs, and global settings.
"""

from django.db import models
from django.conf import settings


class BaseModel(models.Model):
    """Abstract base model with common audit fields."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active  = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.__class__.__name__} - {self.pk}"


# ---------------------------------------------------------------------------
# API Log
# ---------------------------------------------------------------------------
class APILog(BaseModel):
    """Records every inbound API request and its response metadata."""

    METHOD_CHOICES = [
        ('GET',    'GET'),
        ('POST',   'POST'),
        ('PUT',    'PUT'),
        ('PATCH',  'PATCH'),
        ('DELETE', 'DELETE'),
    ]

    endpoint        = models.CharField(max_length=255, help_text='Request URL path.')
    method          = models.CharField(max_length=10, choices=METHOD_CHOICES, help_text='HTTP method.')
    status_code     = models.IntegerField(help_text='HTTP response status code.')
    response_time_ms = models.IntegerField(help_text='Response time in milliseconds.')
    user            = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='api_logs',
        help_text='Authenticated user who made the request, if any.',
    )
    ip_address      = models.GenericIPAddressField(null=True, blank=True,
                        help_text='Client IP address (IPv4 or IPv6).')

    class Meta:
        verbose_name        = 'API Log'
        verbose_name_plural = 'API Logs'
        indexes = [
            models.Index(fields=['endpoint', '-created_at']),
            models.Index(fields=['method',   '-created_at']),
            models.Index(fields=['status_code']),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint} → {self.status_code}"


# ---------------------------------------------------------------------------
# User Activity Log
# ---------------------------------------------------------------------------
class UserActivityLog(models.Model):
    """Tracks meaningful actions performed by users within the application."""

    ACTION_CHOICES = [
        ('login',           'Login'),
        ('logout',          'Logout'),
        ('password_change', 'Password Change'),
        ('profile_update',  'Profile Update'),
        ('settings_change', 'Settings Change'),
        ('data_export',     'Data Export'),
        ('other',           'Other'),
    ]

    user       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='activity_logs',
        help_text='The user who performed the action.',
    )
    action     = models.CharField(
        max_length=50, choices=ACTION_CHOICES,
        db_index=True,
        help_text='Category of the user action.',
    )
    description = models.TextField(
        blank=True,
        help_text='Human-readable description of what the user did.',
    )
    ip_address  = models.GenericIPAddressField(
        null=True, blank=True,
        help_text='Client IP address at the time of the action.',
    )
    metadata    = models.JSONField(
        default=dict, blank=True,
        help_text='Optional structured payload with additional context (e.g. changed fields).',
    )
    created_at  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['user',   '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.action} at {self.created_at:%Y-%m-%d %H:%M}"


# ---------------------------------------------------------------------------
# System Log
# ---------------------------------------------------------------------------
class SystemLog(models.Model):
    """Captures system-level events, errors, and warnings from internal components."""

    LEVEL_CHOICES = [
        ('DEBUG',    'Debug'),
        ('INFO',     'Info'),
        ('WARNING',  'Warning'),
        ('ERROR',    'Error'),
        ('CRITICAL', 'Critical'),
    ]

    level   = models.CharField(
        max_length=10, choices=LEVEL_CHOICES,
        db_index=True,
        help_text='Severity level of the log entry.',
    )
    source  = models.CharField(
        max_length=255,
        db_index=True,
        help_text='Module or component that generated the entry, e.g. `celery.tasks` or `core.middleware`.',
    )
    message = models.TextField(
        help_text='Short, human-readable description of the event.',
    )
    details = models.JSONField(
        default=dict, blank=True,
        help_text='Optional structured payload with traceback, extra context, or metadata.',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering            = ['-created_at']
        indexes = [
            models.Index(fields=['level',  '-created_at']),
            models.Index(fields=['source', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.level}] {self.source}: {self.message[:60]}"


# ---------------------------------------------------------------------------
# System Settings
# ---------------------------------------------------------------------------
class SystemSettings(models.Model):
    """Global runtime configuration stored as key-value pairs."""

    key         = models.CharField(max_length=255, unique=True,
                    help_text='Unique setting key, e.g. `SITE_NAME`.')
    value       = models.TextField(help_text='Setting value.')
    description = models.TextField(blank=True,
                    help_text='Human-readable explanation of the setting.')
    is_sensitive = models.BooleanField(default=False,
                    help_text='Mark true for secrets; value will be masked for non-staff users.')
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'System Setting'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return self.key
