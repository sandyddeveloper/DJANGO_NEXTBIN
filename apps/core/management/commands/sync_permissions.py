"""
Management command to synchronise all *Perms TextChoices to Django's
Permission table and create a Group for every CoreSystemRoles entry.

The SUPER_ADMIN group receives ALL permissions automatically.
Runs automatically on every ``post_migrate`` signal (see CoreConfig).

Usage:
    python manage.py sync_permissions
"""

import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.core.permissions import ALL_PERMISSION_CLASSES, CoreSystemRoles

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync all *Perms TextChoices into Django Permission table and create base Groups."

    def handle(self, *args, **options):
        # Use the contenttypes "auth | group" to namespace the codenames
        ct, _ = ContentType.objects.get_or_create(app_label="auth", model="group")

        # ------------------------------------------------------------------
        # 1. Create / update Permissions
        # ------------------------------------------------------------------
        all_codenames = set()
        for perms_cls in ALL_PERMISSION_CLASSES:
            for codename, label in perms_cls.choices:
                all_codenames.add(codename)
                perm, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=ct,
                    defaults={"name": str(label)},
                )
                if not created and perm.name != str(label):
                    perm.name = str(label)
                    perm.save(update_fields=["name"])

        self.stdout.write(self.style.SUCCESS(f"  [OK] Synced {len(all_codenames)} permissions."))

        # ------------------------------------------------------------------
        # 2. Create Groups for each CoreSystemRoles
        # ------------------------------------------------------------------
        for role in CoreSystemRoles:
            Group.objects.get_or_create(name=role.value)

        self.stdout.write(
            self.style.SUCCESS(
                f"  [OK] Ensured {len(CoreSystemRoles.choices)} system groups exist."
            )
        )

        # ------------------------------------------------------------------
        # 3. Assign ALL permissions to the SUPER_ADMIN group
        # ------------------------------------------------------------------
        try:
            super_admin_group = Group.objects.get(name=CoreSystemRoles.SUPER_ADMIN.value)
            all_perms = Permission.objects.filter(codename__in=all_codenames, content_type=ct)
            super_admin_group.permissions.set(all_perms)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] Assigned {all_perms.count()} permissions to "
                    f"'{CoreSystemRoles.SUPER_ADMIN.value}' group."
                )
            )
        except Group.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    "  [ERROR] SUPER_ADMIN group not found - skipping permission assignment."
                )
            )

        # ------------------------------------------------------------------
        # 4. Assign ALL permissions to the ADMIN group
        # ------------------------------------------------------------------
        try:
            admin_group = Group.objects.get(name=CoreSystemRoles.ADMIN.value)
            admin_group.permissions.set(all_perms)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] Assigned {all_perms.count()} permissions to "
                    f"'{CoreSystemRoles.ADMIN.value}' group."
                )
            )
        except Group.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    "  [ERROR] ADMIN group not found - skipping permission assignment."
                )
            )

        self.stdout.write(self.style.SUCCESS("Permission sync complete."))
