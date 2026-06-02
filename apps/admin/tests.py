import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.constants.authConstant import RoleChoices

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def super_admin(db):
    user = User.objects.create_user(
        email="admin@example.com",
        password="superpassword123",
        first_name="Admin",
        role=RoleChoices.SUPER_ADMIN,
    )
    user.is_verified = True
    user.is_active = True
    user.is_superuser = True
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def standard_user(db):
    user = User.objects.create_user(
        email="user@example.com",
        password="userpassword123",
        first_name="John",
        role=RoleChoices.USER,
    )
    user.is_verified = True
    user.is_active = True
    user.save()
    return user


def _get_or_create_perm(codename, name="Test Permission"):
    """Helper to create a Django Permission tied to auth | group content type."""
    ct, _ = ContentType.objects.get_or_create(app_label="auth", model="group")
    perm, _ = Permission.objects.get_or_create(
        codename=codename, content_type=ct, defaults={"name": name}
    )
    return perm


@pytest.mark.django_db
def test_admin_permissions_forbidden_for_user(api_client, standard_user):
    # Standard user should get 403 Forbidden on admin endpoints
    api_client.force_authenticate(user=standard_user)
    url = reverse("v1:admin-role-list")
    response = api_client.get(url, secure=True)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_list_permissions_by_admin(api_client, super_admin):
    api_client.force_authenticate(user=super_admin)
    url = reverse("v1:admin-permission-list")
    response = api_client.get(url, secure=True)
    assert response.status_code == status.HTTP_200_OK
    # Should return a list of all Django permissions
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_role_crud_by_admin(api_client, super_admin):
    api_client.force_authenticate(user=super_admin)

    # 1. Create Role (Group)
    url = reverse("v1:admin-role-list")
    payload = {"name": "Support Agent"}
    response = api_client.post(url, payload, format="json", secure=True)
    assert response.status_code == status.HTTP_201_CREATED
    role_id = response.data["id"]

    # 2. Assign permission
    perm = _get_or_create_perm("helpdesk", "Helpdesk Access")
    url_assign = reverse("v1:admin-role-assign-permissions", kwargs={"pk": role_id})
    response_assign = api_client.post(
        url_assign, {"permission_ids": [perm.id]}, format="json", secure=True
    )
    assert response_assign.status_code == status.HTTP_200_OK
    assert perm in Group.objects.get(id=role_id).permissions.all()

    # 3. Remove permission
    url_remove = reverse("v1:admin-role-remove-permissions", kwargs={"pk": role_id})
    response_remove = api_client.post(
        url_remove, {"permission_ids": [perm.id]}, format="json", secure=True
    )
    assert response_remove.status_code == status.HTTP_200_OK
    assert perm not in Group.objects.get(id=role_id).permissions.all()

    # 4. Delete Role (Group)
    url_detail = reverse("v1:admin-role-detail", kwargs={"pk": role_id})
    response_delete = api_client.delete(url_detail, secure=True)
    assert response_delete.status_code == status.HTTP_204_NO_CONTENT
    assert not Group.objects.filter(id=role_id).exists()


@pytest.mark.django_db
def test_staff_management_by_admin(api_client, super_admin):
    api_client.force_authenticate(user=super_admin)

    role = Group.objects.create(name="Junior Staff")

    # 1. Create Staff User
    url = reverse("v1:admin-staff-list")
    payload = {
        "email": "staff1@example.com",
        "password": "staffpassword123",
        "first_name": "Jane",
        "last_name": "Smith",
        "role_id": role.id,
    }
    response = api_client.post(url, payload, format="json", secure=True)
    assert response.status_code == status.HTTP_201_CREATED
    staff_code = response.data["profile_code"]

    # Verify user fields
    staff_user = User.objects.get(profile_code=staff_code)
    assert staff_user.is_staff
    assert staff_user.role == RoleChoices.ADMIN
    assert staff_user.assigned_role == role
    assert staff_user.is_verified
    assert staff_user.is_active

    # 2. Assign another role
    role2 = Group.objects.create(name="Senior Staff")
    url_assign = reverse("v1:admin-staff-assign-role", kwargs={"profile_code": staff_code})
    response_assign = api_client.post(url_assign, {"role_id": role2.id}, format="json", secure=True)
    assert response_assign.status_code == status.HTTP_200_OK
    staff_user.refresh_from_db()
    assert staff_user.assigned_role == role2

    # 3. Deactivate staff via DELETE
    url_detail = reverse("v1:admin-staff-detail", kwargs={"profile_code": staff_code})
    response_deactivate = api_client.delete(url_detail, secure=True)
    assert response_deactivate.status_code == status.HTTP_200_OK
    staff_user.refresh_from_db()
    assert not staff_user.is_active
