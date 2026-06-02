from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.exceptions import ValidationError

from apps.authentication.crypto_utils import hash_value
from apps.constants.authConstant import RoleChoices

User = get_user_model()


def create_staff_user(email, password, first_name, last_name, role_id=None):
    """Creates a new staff user account, marked as active and verified.

    Optionally assigns a dynamic Group (role).
    """
    if not email:
        raise ValidationError({"email": "Email is required."})
    if not password:
        raise ValidationError({"password": "Password is required."})

    # Since CustomUser uses email_hashed for unique lookups,
    # we check existence against the hashed email
    email_hash = hash_value(email)
    if User.objects.filter(email_hashed=email_hash).exists():
        raise ValidationError({"email": "A user with this email already exists."})

    assigned_role = None
    if role_id:
        try:
            assigned_role = Group.objects.get(id=role_id)
        except Group.DoesNotExist:
            raise ValidationError({"role_id": "Group (role) matching ID not found."})

    # Create the user using CustomUserManager
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_verified=True,
        is_active=True,
        is_staff=True,
        role=RoleChoices.ADMIN,
        assigned_role=assigned_role,
    )
    user.set_password(password)
    user.save()
    return user


def assign_role_to_staff(user, role_id):
    """Assigns a dynamic Group (role) to an admin/staff member."""
    if user.role == RoleChoices.USER:
        raise ValidationError({"non_field_errors": "Cannot assign roles to regular user accounts."})

    try:
        assigned_role = Group.objects.get(id=role_id)
    except Group.DoesNotExist:
        raise ValidationError({"role_id": "Group (role) matching ID not found."})

    user.assigned_role = assigned_role
    user.save()
    return user
