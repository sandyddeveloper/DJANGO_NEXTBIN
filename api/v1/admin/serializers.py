from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.admin.models import Permission, Role

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "name", "description"]


class RoleSerializer(serializers.ModelSerializer):
    permissions_detail = PermissionSerializer(source="permissions", many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        source="permissions",
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "permissions_detail",
            "permission_ids",
            "created_at",
            "updated_at",
        ]


class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        source="assigned_role",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            "profile_code",
            "email",
            "first_name",
            "last_name",
            "password",
            "role_id",
            "is_active",
        ]
        read_only_fields = ["profile_code"]

    def create(self, validated_data):
        from apps.admin.services import create_staff_user

        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")
        assigned_role = validated_data.get("assigned_role")

        role_id = assigned_role.id if assigned_role else None
        return create_staff_user(email, password, first_name, last_name, role_id)


class RoleAssignSerializer(serializers.Serializer):
    role_id = serializers.PrimaryKeyRelatedField(queryset=Role.objects.filter(is_active=True))


class StaffUserSerializer(serializers.ModelSerializer):
    assigned_role_detail = RoleSerializer(source="assigned_role", read_only=True)

    class Meta:
        model = User
        fields = [
            "profile_code",
            "first_name",
            "last_name",
            "email",
            "email_masked",
            "role",
            "assigned_role_detail",
            "is_verified",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields
