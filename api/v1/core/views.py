from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiParameter, OpenApiResponse, OpenApiExample,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as drf_serializers

from apps.core.models import APILog, UserActivityLog, SystemLog, SystemSettings
from .serializers import (
    APILogSerializer, UserActivityLogSerializer,
    SystemLogSerializer, SystemSettingsSerializer,
)

_HealthResponseSerializer = inline_serializer(
    name='HealthResponse',
    fields={
        'status':  drf_serializers.CharField(help_text='Always "healthy" when reachable.'),
        'message': drf_serializers.CharField(help_text='Human-readable status message.'),
        'version': drf_serializers.CharField(help_text='API version string.'),
    },
)

_PAGINATION_PARAMS = [
    OpenApiParameter('page', OpenApiTypes.INT, OpenApiParameter.QUERY,
                     description='Page number (1-indexed).', required=False),
    OpenApiParameter('page_size', OpenApiTypes.INT, OpenApiParameter.QUERY,
                     description='Number of results per page (default: 20).', required=False),
]


@extend_schema(tags=['System'])
class HealthCheckView(APIView):
    """System health liveness probe."""
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id='system_health_check',
        summary='Health check',
        responses={
            200: OpenApiResponse(
                response=_HealthResponseSerializer,
                description='Service is healthy.',
                examples=[
                    OpenApiExample(
                        'Healthy response',
                        value={'status': 'healthy', 'message': 'API is running', 'version': '1.0.0'},
                        response_only=True,
                    )
                ],
            )
        },
        auth=[],
    )
    def get(self, request):
        return Response(
            {'status': 'healthy', 'message': 'API is running', 'version': '1.0.0'},
            status=status.HTTP_200_OK,
        )


@extend_schema(tags=['Logs — API'])
@extend_schema_view(
    list=extend_schema(
        operation_id='api_logs_list',
        summary='List API request logs',
        parameters=_PAGINATION_PARAMS + [
            OpenApiParameter('endpoint', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('method', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('status_code', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: APILogSerializer(many=True)},
    ),
    retrieve=extend_schema(
        operation_id='api_logs_retrieve',
        summary='Get API log entry by ID',
        responses={
            200: APILogSerializer,
            404: OpenApiResponse(description='Log entry not found.'),
        },
    ),
)
class APILogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset          = APILog.objects.select_related('user').all()
    serializer_class  = APILogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields  = ['endpoint', 'method', 'status_code']
    search_fields     = ['endpoint', 'user__first_name']
    ordering_fields   = ['created_at', 'response_time_ms', 'status_code']
    ordering          = ['-created_at']


@extend_schema(tags=['Logs — User Activity'])
@extend_schema_view(
    list=extend_schema(
        operation_id='user_activity_logs_list',
        summary='List user activity logs',
        parameters=_PAGINATION_PARAMS + [
            OpenApiParameter('action', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('user', OpenApiTypes.INT, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: UserActivityLogSerializer(many=True)},
    ),
    retrieve=extend_schema(
        operation_id='user_activity_logs_retrieve',
        summary='Get user activity log entry by ID',
        responses={
            200: UserActivityLogSerializer,
            404: OpenApiResponse(description='Activity log entry not found.'),
        },
    ),
)
class UserActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = UserActivityLog.objects.select_related('user').all()
    serializer_class   = UserActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['action', 'user']
    search_fields      = ['user__first_name', 'user__email', 'description']
    ordering_fields    = ['created_at']
    ordering           = ['-created_at']


@extend_schema(tags=['Logs — System'])
@extend_schema_view(
    list=extend_schema(
        operation_id='system_logs_list',
        summary='List system logs',
        parameters=_PAGINATION_PARAMS + [
            OpenApiParameter('level', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('source', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: SystemLogSerializer(many=True)},
    ),
    retrieve=extend_schema(
        operation_id='system_logs_retrieve',
        summary='Get system log entry by ID',
        responses={
            200: SystemLogSerializer,
            404: OpenApiResponse(description='System log entry not found.'),
        },
    ),
)
class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset           = SystemLog.objects.all()
    serializer_class   = SystemLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['level', 'source']
    search_fields      = ['source', 'message']
    ordering_fields    = ['created_at']
    ordering           = ['-created_at']


@extend_schema(tags=['System Settings'])
@extend_schema_view(
    list=extend_schema(
        operation_id='settings_list',
        summary='List system settings',
        parameters=[
            OpenApiParameter('key', OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_sensitive', OpenApiTypes.BOOL, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: SystemSettingsSerializer(many=True)},
    ),
    retrieve=extend_schema(
        operation_id='settings_retrieve',
        summary='Get setting by ID',
        responses={
            200: SystemSettingsSerializer,
            404: OpenApiResponse(description='Setting not found.'),
        },
    ),
    create=extend_schema(
        operation_id='settings_create',
        summary='Create a setting',
        request=SystemSettingsSerializer,
        responses={
            201: SystemSettingsSerializer,
            400: OpenApiResponse(description='Validation error.'),
        },
    ),
    update=extend_schema(
        operation_id='settings_update',
        summary='Replace a setting (full update)',
        request=SystemSettingsSerializer,
        responses={200: SystemSettingsSerializer, 400: OpenApiResponse(description='Validation error.')},
    ),
    partial_update=extend_schema(
        operation_id='settings_partial_update',
        summary='Update a setting (partial)',
        request=SystemSettingsSerializer,
        responses={200: SystemSettingsSerializer, 400: OpenApiResponse(description='Validation error.')},
    ),
    destroy=extend_schema(
        operation_id='settings_destroy',
        summary='Delete a setting',
        responses={
            204: OpenApiResponse(description='Deleted.'),
            404: OpenApiResponse(description='Setting not found.'),
        },
    ),
)
class SystemSettingsViewSet(viewsets.ModelViewSet):
    queryset           = SystemSettings.objects.all()
    serializer_class   = SystemSettingsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields   = ['key', 'is_sensitive']
    search_fields      = ['key', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_sensitive=False)
        return qs
