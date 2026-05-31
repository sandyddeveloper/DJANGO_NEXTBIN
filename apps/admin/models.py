from django.db import models


class Permission(models.Model):
    """Dynamic system permissions that can be mapped to custom staff roles."""

    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique permission code, e.g. 'view_api_logs'.",
    )
    name = models.CharField(max_length=100, help_text="Human-readable name of the permission.")
    description = models.TextField(
        blank=True, help_text="Detailed description of what this permission grants."
    )

    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(models.Model):
    """Dynamic roles created and configured by administrators."""

    name = models.CharField(max_length=100, unique=True, help_text="Unique name of the role.")
    description = models.TextField(blank=True, help_text="Description of the role's purpose.")
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
        help_text="Permissions assigned to this role.",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Active roles can be assigned to staff.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
