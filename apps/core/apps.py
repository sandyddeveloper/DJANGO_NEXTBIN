"""
Core app configuration.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        from django.db.models.signals import post_migrate

        post_migrate.connect(_sync_permissions_handler, sender=self)


def _sync_permissions_handler(sender, **kwargs):
    """Auto-sync permissions after every migration."""
    from django.core.management import call_command

    call_command("sync_permissions", verbosity=0)
