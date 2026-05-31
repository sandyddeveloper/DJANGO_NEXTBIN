from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.core.models import APILog, SystemLog, SystemSettings, UserActivityLog

User = get_user_model()


class APILogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(
        source="user.username",
        read_only=True,
        allow_null=True,
        help_text="Username of the authenticated user. `null` for anonymous requests.",
    )

    class Meta:
        model = APILog
        fields = [
            "id",
            "endpoint",
            "method",
            "status_code",
            "response_time_ms",
            "user",
            "user_username",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
        extra_kwargs = {
            "id": {"help_text": "Unique log entry ID."},
            "endpoint": {"help_text": "Request URL path."},
            "method": {"help_text": "HTTP method: `GET`, `POST`, etc."},
            "status_code": {"help_text": "HTTP response status code."},
            "response_time_ms": {"help_text": "Response time in milliseconds."},
            "user": {"help_text": "ID of the authenticated user; `null` if anonymous."},
            "ip_address": {"help_text": "Client IP address."},
            "created_at": {"help_text": "UTC timestamp when the log was recorded."},
        }


class UserActivityLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(
        source="user.first_name",  # or email since custom user does not have username
        read_only=True,
        help_text="Name of the user who performed the action.",
    )
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
        help_text="Email address of the user.",
    )
    action_display = serializers.CharField(
        source="get_action_display",
        read_only=True,
        help_text="Human-readable label for the action.",
    )

    class Meta:
        model = UserActivityLog
        fields = [
            "id",
            "user",
            "user_username",
            "user_email",
            "action",
            "action_display",
            "description",
            "ip_address",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
        extra_kwargs = {
            "id": {"help_text": "Unique activity log entry ID."},
            "user": {"help_text": "ID of the user who performed the action."},
            "action": {"help_text": "Action category key, e.g. `login`, `logout`."},
            "description": {"help_text": "Free-text description of what the user did."},
            "ip_address": {"help_text": "Client IP address at the time of the action."},
            "metadata": {"help_text": "Optional JSON payload with extra context."},
            "created_at": {"help_text": "UTC timestamp when the activity was recorded."},
        }


class SystemLogSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(
        source="get_level_display",
        read_only=True,
        help_text="Human-readable severity label.",
    )

    class Meta:
        model = SystemLog
        fields = [
            "id",
            "level",
            "level_display",
            "source",
            "message",
            "details",
            "created_at",
        ]
        read_only_fields = fields
        extra_kwargs = {
            "id": {"help_text": "Unique system log entry ID."},
            "level": {
                "help_text": "Severity level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`."
            },
            "source": {"help_text": "Module or component that generated the log."},
            "message": {"help_text": "Short description of the event."},
            "details": {"help_text": "Optional JSON payload with traceback or extra context."},
            "created_at": {"help_text": "UTC timestamp when the event was recorded."},
        }


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ["id", "key", "value", "description", "is_sensitive", "updated_at"]
        read_only_fields = ["id", "updated_at"]
        extra_kwargs = {
            "id": {"help_text": "Unique setting ID."},
            "key": {"help_text": "Unique identifier for the setting."},
            "value": {
                "write_only": True,
                "help_text": (
                    "The setting value (write-only). "
                    "Sensitive values are masked in responses."
                ),
            },
            "description": {"help_text": "Explanation of what the setting controls."},
            "is_sensitive": {"help_text": "If true, the value is hidden from non-staff users."},
            "updated_at": {"help_text": "UTC timestamp of the last modification."},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if instance.is_sensitive and request and not request.user.is_staff:
            data["value"] = "***HIDDEN***"
        return data
