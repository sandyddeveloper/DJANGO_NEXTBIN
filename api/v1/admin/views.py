from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiResponse
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin.models import Permission, Role
from apps.constants.authConstant import RoleChoices

from .serializers import (
    PermissionSerializer,
    RoleAssignSerializer,
    RoleSerializer,
    StaffCreateSerializer,
    StaffUserSerializer,
)

User = get_user_model()


class IsSuperAdmin(BasePermission):
    """Allows access only to Super Admins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == RoleChoices.SUPER_ADMIN
        )


class PermissionListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = PermissionSerializer

    @extend_schema(
        operation_id="permissions_list",
        summary="List permissions",
        responses={200: PermissionSerializer(many=True)},
        tags=["Permissions"]
    )
    def get(self, request):
        queryset = Permission.objects.all().order_by("code")
        serializer = PermissionSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="permissions_create",
        summary="Create a permission",
        request=PermissionSerializer,
        responses={201: PermissionSerializer},
        tags=["Permissions"]
    )
    def post(self, request):
        serializer = PermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PermissionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
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
        tags=["Permissions"]
    )
    def get(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermissionSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)



    @extend_schema(
        operation_id="permissions_partial_update",
        summary="Update a permission (partial)",
        request=PermissionSerializer,
        responses={200: PermissionSerializer},
        tags=["Permissions"]
    )
    def patch(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermissionSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="permissions_destroy",
        summary="Delete a permission",
        tags=["Permissions"]
    )
    def delete(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = RoleSerializer

    @extend_schema(
        operation_id="roles_list",
        summary="List roles",
        responses={200: RoleSerializer(many=True)},
        tags=["Roles"]
    )
    def get(self, request):
        queryset = Role.objects.all().order_by("name")
        serializer = RoleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="roles_create",
        summary="Create a role",
        request=RoleSerializer,
        responses={201: RoleSerializer},
        tags=["Roles"]
    )
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = RoleSerializer

    def get_object(self, pk):
        try:
            return Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return None

    @extend_schema(
        operation_id="roles_retrieve",
        summary="Get role by ID",
        responses={200: RoleSerializer},
        tags=["Roles"]
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
        tags=["Roles"]
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
        summary="Deactivate a role",
        tags=["Roles"]
    )
    def delete(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_active = False
        obj.save()
        return Response(
            {"message": f"Role '{obj.name}' deactivated successfully."},
            status=status.HTTP_200_OK
        )


class RolePermissionsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = RoleSerializer
    action = None  # "assign" or "remove", set via as_view()

    @extend_schema(
        summary="Assign or remove permissions for a role",
        request=inline_serializer(
            name="RolePermissionsPayload",
            fields={
                "permission_ids": drf_serializers.ListField(
                    child=drf_serializers.IntegerField(),
                    help_text="List of permission IDs."
                )
            }
        ),
        responses={200: RoleSerializer},
        tags=["Roles"]
    )
    def post(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
        except Role.DoesNotExist:
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


class StaffListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = StaffUserSerializer

    @extend_schema(
        operation_id="staff_list",
        summary="List staff members",
        responses={200: StaffUserSerializer(many=True)},
        tags=["Staff"]
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
        tags=["Staff"]
    )
    def post(self, request):
        serializer = StaffCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = StaffUserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = StaffUserSerializer

    def get_object(self, pk):
        try:
            return User.objects.get(is_staff=True, pk=pk)
        except User.DoesNotExist:
            return None

    @extend_schema(
        operation_id="staff_retrieve",
        summary="Get staff member by ID",
        responses={200: StaffUserSerializer},
        tags=["Staff"]
    )
    def get(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffUserSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="staff_partial_update",
        summary="Update a staff member (partial)",
        request=StaffUserSerializer,
        responses={200: StaffUserSerializer},
        tags=["Staff"]
    )
    def patch(self, request, pk):
        obj = self.get_object(pk)
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
        tags=["Staff"]
    )
    def post(self, request, pk):
        obj = self.get_object(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_active = False
        obj.save()
        return Response(
            {"message": f"Staff user {obj.profile_code} deactivated successfully."},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="staff_destroy",
        summary="Deactivate a staff user via DELETE",
        responses={200: OpenApiResponse(description="Staff user deactivated successfully.")},
        tags=["Staff"]
    )
    def delete(self, request, pk):
        return self.post(request, pk)


class StaffAssignRoleView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    serializer_class = StaffUserSerializer

    @extend_schema(
        operation_id="staff_assign_role",
        summary="Assign a role to a staff member",
        request=RoleAssignSerializer,
        responses={200: StaffUserSerializer},
        tags=["Staff"]
    )
    def post(self, request, pk):
        try:
            user = User.objects.get(is_staff=True, pk=pk)
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



