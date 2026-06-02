from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import (
    HasActivePermission,
    RolePerms,
    StaffPerms,
)

from .serializers import (
    PermissionSerializer,
    RoleAssignSerializer,
    RoleSerializer,
    StaffCreateSerializer,
    StaffUserSerializer,
)

User = get_user_model()


# ── Permissions ─────────────────────────────────────────────────────────────

class PermissionListView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(RolePerms.MANAGE_PERMISSIONS)]
    serializer_class = PermissionSerializer

    @extend_schema(
        operation_id="permissions_list",
        summary="List permissions",
        responses={200: PermissionSerializer(many=True)},
        tags=["Permissions"],
    )
    def get(self, request):
        queryset = Permission.objects.all().order_by("codename")
        serializer = PermissionSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PermissionDetailView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(RolePerms.MANAGE_PERMISSIONS)]
    serializer_class = PermissionSerializer

    def get_object(self, pk):
        try:
            return Permission.objects.get(pk=pk)
        except Permission.DoesNotExist:
            return None

    @extend_schema(
        operation_id="permissions_retrieve",
        summary="Get permission by ID",
        responses={200: PermissionSerializer},
        tags=["Permissions"],
    )
    def get(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermissionSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Roles (Django Groups) ──────────────────────────────────────────────────

class RoleListView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(RolePerms.VIEW_ROLES)]
    serializer_class = RoleSerializer

    @extend_schema(
        operation_id="roles_list",
        summary="List roles",
        responses={200: RoleSerializer(many=True)},
        tags=["Roles"],
    )
    def get(self, request):
        queryset = Group.objects.all().order_by("name")
        serializer = RoleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="roles_create",
        summary="Create a role",
        request=RoleSerializer,
        responses={201: RoleSerializer},
        tags=["Roles"],
    )
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleDetailView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(RolePerms.MANAGE_ROLES)]
    serializer_class = RoleSerializer

    def get_object(self, pk):
        try:
            return Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return None

    @extend_schema(
        operation_id="roles_retrieve",
        summary="Get role by ID",
        responses={200: RoleSerializer},
        tags=["Roles"],
    )
    def get(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = RoleSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="roles_partial_update",
        summary="Update a role (partial)",
        request=RoleSerializer,
        responses={200: RoleSerializer},
        tags=["Roles"],
    )
    def patch(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = RoleSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="roles_destroy",
        summary="Delete a role",
        tags=["Roles"],
    )
    def delete(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolePermissionsView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(RolePerms.MANAGE_PERMISSIONS)]
    serializer_class = RoleSerializer
    action = None  # "assign" or "remove", set via as_view()

    @extend_schema(
        summary="Assign or remove permissions for a role",
        request=inline_serializer(
            name="RolePermissionsPayload",
            fields={
                "permission_ids": drf_serializers.ListField(
                    child=drf_serializers.IntegerField(),
                    help_text="List of permission IDs.",
                )
            },
        ),
        responses={200: RoleSerializer},
        tags=["Roles"],
    )
    def post(self, request, pk):
        try:
            role = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        permission_ids = request.data.get("permission_ids", [])
        if not isinstance(permission_ids, list):
            return Response(
                {"error": "permission_ids must be a list of integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        perms = Permission.objects.filter(id__in=permission_ids)
        if self.action == "remove":
            role.permissions.remove(*perms)
        else:
            role.permissions.add(*perms)
        role.save()

        serializer = RoleSerializer(role)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Staff ───────────────────────────────────────────────────────────────────

class StaffListView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(StaffPerms.VIEW_STAFF)]
    serializer_class = StaffUserSerializer

    @extend_schema(
        operation_id="staff_list",
        summary="List staff members",
        responses={200: StaffUserSerializer(many=True)},
        tags=["Staff"],
    )
    def get(self, request):
        queryset = User.objects.filter(is_staff=True).order_by("profile_code")
        serializer = StaffUserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="staff_create",
        summary="Create a staff user",
        request=StaffCreateSerializer,
        responses={201: StaffUserSerializer},
        tags=["Staff"],
    )
    def post(self, request):
        serializer = StaffCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = StaffUserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetailView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(StaffPerms.MANAGE_STAFF)]
    serializer_class = StaffUserSerializer

    def get_object(self, profile_code):
        try:
            return User.objects.get(is_staff=True, profile_code=profile_code)
        except User.DoesNotExist:
            return None

    @extend_schema(
        operation_id="staff_retrieve",
        summary="Get staff member by ID",
        responses={200: StaffUserSerializer},
        tags=["Staff"],
    )
    def get(self, request, profile_code):
        obj = self.get_object(profile_code)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffUserSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="staff_partial_update",
        summary="Update a staff member (partial)",
        request=StaffUserSerializer,
        responses={200: StaffUserSerializer},
        tags=["Staff"],
    )
    def patch(self, request, profile_code):
        obj = self.get_object(profile_code)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffUserSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="staff_deactivate",
        summary="Deactivate a staff user",
        responses={200: OpenApiResponse(description="Staff user deactivated successfully.")},
        tags=["Staff"],
    )
    def delete(self, request, profile_code):
        obj = self.get_object(profile_code)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_active = False
        obj.save()
        return Response(
            {"message": f"Staff user {obj.profile_code} deactivated successfully."},
            status=status.HTTP_200_OK,
        )


class StaffAssignRoleView(APIView):
    permission_classes = [IsAuthenticated, HasActivePermission(StaffPerms.ASSIGN_ROLES)]
    serializer_class = StaffUserSerializer

    @extend_schema(
        operation_id="staff_assign_role",
        summary="Assign a role to a staff member",
        request=RoleAssignSerializer,
        responses={200: StaffUserSerializer},
        tags=["Staff"],
    )
    def post(self, request, profile_code):
        try:
            user = User.objects.get(is_staff=True, profile_code=profile_code)
        except User.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleAssignSerializer(data=request.data)
        if serializer.is_valid():
            from apps.admin.services import assign_role_to_staff

            role_id = serializer.validated_data["role_id"].id
            user = assign_role_to_staff(user, role_id)

            response_serializer = StaffUserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
