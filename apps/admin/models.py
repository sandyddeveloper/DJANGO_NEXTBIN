"""
Admin models module.

Custom Permission and Role models have been replaced by Django's built-in
``django.contrib.auth.models.Permission`` and ``django.contrib.auth.models.Group``.

All permission codenames are defined in ``apps.core.permissions`` as TextChoices
and auto-synced to the database via the ``sync_permissions`` management command.
"""
