"""
Dynamic Permissions System for NextBin.

Defines a self-discovering permission framework where:
- *Perms TextChoices classes declare all codenames (single source of truth).
- HasActivePermission checks the user's assigned Group (role) against cached permissions.
- ScreenRegistry dynamically builds a permissions matrix for frontend role-based UI control.
- Cache invalidation signals ensure Redis/in-memory cache stays fresh.

Role Hierarchy:  SUPER_ADMIN > ADMIN > [Dynamic Groups] > USER
"""

import inspect
import sys

from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import models
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from rest_framework import permissions


# ---------------------------------------------------------------------------
# Cache timeout constants (seconds)
# ---------------------------------------------------------------------------
CACHE_TIMEOUT_HIGH = 3600  # 1 hour


# ===========================================================================
# Core System Roles
# ===========================================================================

class CoreSystemRoles(models.TextChoices):
    """
    Static base roles stored on CustomUser.role.
    Dynamic Groups (with granular permissions) sit between ADMIN and USER.
    """
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    ADMIN = "ADMIN", "Admin"
    USER = "USER", "User"


# ===========================================================================
# HasActivePermission — the primary view guard
# ===========================================================================

class HasActivePermission(permissions.BasePermission):
    """
    Validates whether the authenticated user's role / assigned group
    has the required permission codename.

    Usage::

        permission_classes = [IsAuthenticated, HasActivePermission(LogPerms.VIEW_API_LOGS)]

    Behaviour:
    1. Unauthenticated → denied.
    2. SUPER_ADMIN role → always granted (bypass).
    3. Otherwise, check the user's ``assigned_role`` (Django Group)
       permissions via cache → DB fallback.
    """

    def __init__(self, required_permission):
        # Accept both TextChoices members and raw strings.
        self.required_permission = getattr(required_permission, "value", required_permission)

    def __call__(self):
        """Allow ``HasActivePermission(...)`` inside a list (DRF instantiates)."""
        return self

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        active_role = getattr(user, "role", None)
        if not active_role:
            return False

        # ---- Super Admin bypass ----
        if active_role == CoreSystemRoles.SUPER_ADMIN:
            return True

        # ---- Admin bypass (full access like super admin) ----
        if active_role == CoreSystemRoles.ADMIN:
            return True

        # ---- Dynamic group permission check ----
        assigned_role = getattr(user, "assigned_role", None)
        if not assigned_role:
            return False

        cache_key = f"role_perms_{assigned_role.name.replace(' ', '_').upper()}"
        role_perms = cache.get(cache_key)

        if role_perms is None:
            # Fallback to DB
            try:
                group = Group.objects.prefetch_related("permissions").get(pk=assigned_role.pk)
                role_perms = set(group.permissions.values_list("codename", flat=True))
            except Group.DoesNotExist:
                role_perms = set()
            cache.set(cache_key, role_perms, timeout=CACHE_TIMEOUT_HIGH)

        return self.required_permission in role_perms


# ===========================================================================
# ScreenRegistry — dynamic permissions matrix for frontend
# ===========================================================================

class ScreenRegistry:
    """
    Dynamically builds a permissions matrix by scanning all ``*Perms``
    TextChoices classes in this module.  Used by the frontend to toggle
    UI components per-role.
    """

    @classmethod
    def get_dynamic_matrix(cls) -> dict:
        screens = {}

        for obj in ALL_PERMISSION_CLASSES:
            name = obj.__name__
            screen_key = name[:-5].lower()  # e.g. 'LogPerms' → 'log'

            screen_permission = None
            components = {}

            for codename, description in obj.choices:
                if codename.startswith(("view_", "access_", "list_")):
                    if not screen_permission:
                        screen_permission = codename
                    components[codename] = codename
                else:
                    components[codename] = codename

            if not screen_permission and obj.choices:
                screen_permission = obj.choices[0][0]

            screens[screen_key] = {
                "permission": screen_permission,
                "components": components,
            }

        return {"screens": screens}

    @classmethod
    def get_role_permissions(cls, role_name: str) -> set:
        role_upper = role_name.replace(" ", "_").upper() if role_name else ""
        if not role_upper:
            return set()

        cache_key = f"role_perms_{role_upper}"
        role_perms = cache.get(cache_key)

        if role_perms is None:
            group = (
                Group.objects.prefetch_related("permissions")
                .filter(name__iexact=role_name)
                .first()
            )
            if group:
                role_perms = set(group.permissions.values_list("codename", flat=True))
                cache.set(cache_key, role_perms, timeout=CACHE_TIMEOUT_HIGH)
            else:
                role_perms = set()

        return role_perms

    @classmethod
    def generate_for_role(cls, role_name: str) -> dict:
        role_upper = role_name.upper() if role_name else ""
        is_super = role_upper == CoreSystemRoles.SUPER_ADMIN.value
        is_admin = role_upper == CoreSystemRoles.ADMIN.value

        role_perms = cls.get_role_permissions(role_name)
        matrix = cls.get_dynamic_matrix()

        user_screens = {}
        for screen_key, config in matrix["screens"].items():
            req_perm = config.get("permission")
            has_screen_access = is_super or is_admin or (req_perm is None) or (req_perm in role_perms)

            components_data = {}
            has_any_available = False

            for comp_key, req_comp_perm in config.get("components", {}).items():
                has_comp = is_super or is_admin or (req_comp_perm is None) or (req_comp_perm in role_perms)
                components_data[comp_key] = {"is_available": has_comp}
                if has_comp:
                    has_any_available = True

            if config.get("components"):
                screen_available = has_any_available
            else:
                screen_available = has_screen_access

            user_screens[screen_key] = {
                "is_available": screen_available,
                "components": components_data,
            }

        return {"active_role": role_upper, "screens": user_screens}


# ===========================================================================
# Permission TextChoices — single source of truth for every codename
# ===========================================================================

"""
Naming Convention:
- Module + Perms  (e.g. UserPerms, StaffPerms, LogPerms)
- Operation prefixes: View, Manage, Create, Delete, Modify, Approve, Execute
"""


class UserPerms(models.TextChoices):
    VIEW_USERS = "view_users", "Can view user profiles"
    MANAGE_USERS = "manage_users", "Can create, edit, and deactivate user profiles"


class StaffPerms(models.TextChoices):
    VIEW_STAFF = "view_staff", "Can view staff / dynamic-role users"
    MANAGE_STAFF = "manage_staff", "Can create, edit, and deactivate staff users"
    ASSIGN_ROLES = "assign_staff_roles", "Can assign dynamic roles to staff"


class RolePerms(models.TextChoices):
    VIEW_ROLES = "view_roles", "Can view roles and their permissions"
    MANAGE_ROLES = "manage_roles", "Can create, edit, and deactivate roles"
    MANAGE_PERMISSIONS = "manage_permissions", "Can assign and remove permissions from roles"


class LogPerms(models.TextChoices):
    VIEW_API_LOGS = "view_api_logs", "Can view API request logs"
    VIEW_ACTIVITY_LOGS = "view_activity_logs", "Can view user activity logs"
    VIEW_SYSTEM_LOGS = "view_system_logs", "Can view system logs"


class SettingsPerms(models.TextChoices):
    VIEW_SETTINGS = "view_settings", "Can view system settings"
    MANAGE_SETTINGS = "manage_settings", "Can create, edit, and delete system settings"


# ===========================================================================
# Auto-discovery of all *Perms classes
# ===========================================================================

ALL_CUSTOM_PERMS_CODENAMES: set = set()
ALL_PERMISSION_CLASSES: list = []

for _name, _obj in inspect.getmembers(sys.modules[__name__]):
    if (
        inspect.isclass(_obj)
        and issubclass(_obj, models.TextChoices)
        and _name.endswith("Perms")
    ):
        ALL_CUSTOM_PERMS_CODENAMES.update(_obj.values)
        ALL_PERMISSION_CLASSES.append(_obj)


# ===========================================================================
# Cache Invalidation Signals
# ===========================================================================

@receiver(post_save, sender=Group)
def invalidate_group_perms_cache_on_save(sender, instance, **kwargs):
    """Invalidate cache when a Group (role) is renamed or updated."""
    cache_key = f"role_perms_{instance.name.replace(' ', '_').upper()}"
    cache.delete(cache_key)


@receiver(post_delete, sender=Group)
def invalidate_group_perms_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when a Group (role) is deleted."""
    cache_key = f"role_perms_{instance.name.replace(' ', '_').upper()}"
    cache.delete(cache_key)


@receiver(m2m_changed, sender=Group.permissions.through)
def invalidate_group_perms_cache_on_m2m_change(sender, instance, action, **kwargs):
    """Invalidate cache when permissions are added/removed/cleared from a Group."""
    if action in ("post_add", "post_remove", "post_clear"):
        cache_key = f"role_perms_{instance.name.replace(' ', '_').upper()}"
        cache.delete(cache_key)
