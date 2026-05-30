from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.authentication.crypto_utils import hash_value

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if none exists'

    def handle(self, *args, **options):
        if not User.objects.filter(email_hashed=hash_value('admin@example.com')).exists():
            # Create a superuser matching our custom user model fields
            User.objects.create_superuser(
                email='admin@example.com',
                password='admin',
                first_name='Admin',
                role='SUPER_ADMIN'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))
