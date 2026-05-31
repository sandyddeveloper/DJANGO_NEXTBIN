import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Return a test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test'
    )


@pytest.fixture
def admin_user(db):
    """Return a test admin user."""
    return User.objects.create_superuser(
        email='admin@example.com',
        password='admin123',
        first_name='Admin'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an authenticated admin API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client
