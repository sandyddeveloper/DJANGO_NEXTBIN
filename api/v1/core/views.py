from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import APILog, SystemLog, SystemSettings, UserActivityLog

from .serializers import (
    APILogSerializer,
    SystemLogSerializer,
    SystemSettingsSerializer,
    UserActivityLogSerializer,
)

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

_HealthResponseSerializer = inline_serializer(
    name="HealthResponse",
    fields={
        "status": drf_serializers.CharField(help_text='Always "healthy" when reachable.'),
        "message": drf_serializers.CharField(help_text="Human-readable status message."),
        "version": drf_serializers.CharField(help_text="API version string."),
    },
)

_PAGINATION_PARAMS = [
    OpenApiParameter(
        "page",
        OpenApiTypes.INT,
        OpenApiParameter.QUERY,
        description="Page number (1-indexed).",
        required=False,
    ),
    OpenApiParameter(
        "page_size",
        OpenApiTypes.INT,
        OpenApiParameter.QUERY,
        description="Number of results per page (default: 20).",
        required=False,
    ),
]


@extend_schema(tags=["System"])
class HealthCheckView(APIView):
    """System health liveness probe."""

    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="system_health_check",
        summary="Health check",
        responses={
            200: OpenApiResponse(
                response=_HealthResponseSerializer,
                description="Service is healthy.",
                examples=[
                    OpenApiExample(
                        "Healthy response",
                        value={
                            "status": "healthy",
                            "message": "API is running",
                            "version": "1.0.0",
                        },
                        response_only=True,
                    )
                ],
            )
        },
        auth=[],
    )
    def get(self, request):
        return Response(
            {"status": "healthy", "message": "API is running", "version": "1.0.0"},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=["Logs — API"])
class APILogListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = APILogSerializer

    @extend_schema(
        operation_id="api_logs_list",
        summary="List API request logs",
        parameters=_PAGINATION_PARAMS + [
            OpenApiParameter("endpoint", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("method", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("status_code", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: APILogSerializer(many=True)},
    )
    def get(self, request):
        queryset = APILog.objects.select_related("user").all().order_by("-created_at")

        # Filtering
        endpoint = request.query_params.get("endpoint")
        method = request.query_params.get("method")
        status_code = request.query_params.get("status_code")
        if endpoint:
            queryset = queryset.filter(endpoint__icontains=endpoint)
        if method:
            queryset = queryset.filter(method__iexact=method)
        if status_code:
            queryset = queryset.filter(status_code=status_code)

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(endpoint__icontains=search) |
                Q(user__first_name__icontains=search)
            )

        # Ordering
        ordering = request.query_params.get("ordering")
        if ordering in ["created_at", "-created_at", "response_time_ms", "-response_time_ms", "status_code", "-status_code"]:
            queryset = queryset.order_by(ordering)

        # Pagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = APILogSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = APILogSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Logs — API"])
class APILogDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = APILogSerializer

    @extend_schema(
        operation_id="api_logs_retrieve",
        summary="Get API log entry by ID",
        responses={
            200: APILogSerializer,
            404: OpenApiResponse(description="Log entry not found."),
        },
    )
    def get(self, request, pk):
        try:
            log = APILog.objects.select_related("user").get(pk=pk)
            serializer = APILogSerializer(log)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except APILog.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["Logs — User Activity"])
class UserActivityLogListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserActivityLogSerializer

    @extend_schema(
        operation_id="user_activity_logs_list",
        summary="List user activity logs",
        parameters=_PAGINATION_PARAMS + [
            OpenApiParameter("action", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("user", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: UserActivityLogSerializer(many=True)},
    )
    def get(self, request):
        queryset = UserActivityLog.objects.select_related("user").all().order_by("-created_at")

        # Filtering
        action = request.query_params.get("action")
        user_id = request.query_params.get("user")
        if action:
            queryset = queryset.filter(action=action)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(description__icontains=search)
            )

        # Ordering
        ordering = request.query_params.get("ordering")
        if ordering in ["created_at", "-created_at"]:
            queryset = queryset.order_by(ordering)

        # Pagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = UserActivityLogSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = UserActivityLogSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Logs — User Activity"])
class UserActivityLogDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserActivityLogSerializer

    @extend_schema(
        operation_id="user_activity_logs_retrieve",
        summary="Get user activity log entry by ID",
        responses={
            200: UserActivityLogSerializer,
            404: OpenApiResponse(description="Activity log entry not found."),
        },
    )
    def get(self, request, pk):
        try:
            log = UserActivityLog.objects.select_related("user").get(pk=pk)
            serializer = UserActivityLogSerializer(log)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserActivityLog.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["Logs — System"])
class SystemLogListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SystemLogSerializer

    @extend_schema(
        operation_id="system_logs_list",
        summary="List system logs",
        parameters=_PAGINATION_PARAMS + [
            OpenApiParameter("level", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("source", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: SystemLogSerializer(many=True)},
    )
    def get(self, request):
        queryset = SystemLog.objects.all().order_by("-created_at")

        # Filtering
        level = request.query_params.get("level")
        source = request.query_params.get("source")
        if level:
            queryset = queryset.filter(level=level)
        if source:
            queryset = queryset.filter(source=source)

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(source__icontains=search) |
                Q(message__icontains=search)
            )

        # Ordering
        ordering = request.query_params.get("ordering")
        if ordering in ["created_at", "-created_at"]:
            queryset = queryset.order_by(ordering)

        # Pagination
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = SystemLogSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = SystemLogSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Logs — System"])
class SystemLogDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SystemLogSerializer

    @extend_schema(
        operation_id="system_logs_retrieve",
        summary="Get system log entry by ID",
        responses={
            200: SystemLogSerializer,
            404: OpenApiResponse(description="System log entry not found."),
        },
    )
    def get(self, request, pk):
        try:
            log = SystemLog.objects.get(pk=pk)
            serializer = SystemLogSerializer(log)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SystemLog.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=["System Settings"])
class SystemSettingsListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SystemSettingsSerializer

    def get_queryset(self, request):
        qs = SystemSettings.objects.all()
        if not request.user.is_staff:
            qs = qs.filter(is_sensitive=False)
        return qs

    @extend_schema(
        operation_id="settings_list",
        summary="List system settings",
        parameters=[
            OpenApiParameter("key", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter("is_sensitive", OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: SystemSettingsSerializer(many=True)},
    )
    def get(self, request):
        queryset = self.get_queryset(request)

        # Filtering
        key = request.query_params.get("key")
        is_sensitive = request.query_params.get("is_sensitive")
        if key:
            queryset = queryset.filter(key__icontains=key)
        if is_sensitive:
            val = is_sensitive.lower() in ["true", "1"]
            queryset = queryset.filter(is_sensitive=val)

        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(key__icontains=search) |
                Q(description__icontains=search)
            )

        serializer = SystemSettingsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="settings_create",
        summary="Create a setting",
        request=SystemSettingsSerializer,
        responses={
            201: SystemSettingsSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def post(self, request):
        serializer = SystemSettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["System Settings"])
class SystemSettingsDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SystemSettingsSerializer

    def get_object(self, request, pk):
        try:
            obj = SystemSettings.objects.get(pk=pk)
            if not request.user.is_staff and obj.is_sensitive:
                return None
            return obj
        except SystemSettings.DoesNotExist:
            return None

    @extend_schema(
        operation_id="settings_retrieve",
        summary="Get setting by ID",
        responses={
            200: SystemSettingsSerializer,
            404: OpenApiResponse(description="Setting not found."),
        },
    )
    def get(self, request, pk):
        obj = self.get_object(request, pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SystemSettingsSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)



    @extend_schema(
        operation_id="settings_partial_update",
        summary="Update a setting (partial)",
        request=SystemSettingsSerializer,
        responses={
            200: SystemSettingsSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def patch(self, request, pk):
        obj = self.get_object(request, pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = SystemSettingsSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        operation_id="settings_destroy",
        summary="Delete a setting",
        responses={
            204: OpenApiResponse(description="Deleted."),
            404: OpenApiResponse(description="Setting not found."),
        },
    )
    def delete(self, request, pk):
        obj = self.get_object(request, pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
