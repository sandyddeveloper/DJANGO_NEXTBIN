from django.urls import path
from api.v1.users.views import (
    SignupView,
    VerifyOTPView,
    ResendOTPView,
    ForgotPasswordView,
    ResetPasswordView,
    ForgotPinView,
    ResetPinView,
    LoginView,
    TokenRefreshView,
    UserProfileView,
    UserProfileViewSet,
)
from api.v1.core.views import (
    HealthCheckView,
    APILogViewSet,
    UserActivityLogViewSet,
    SystemLogViewSet,
    SystemSettingsViewSet,
)

app_name = 'v1'

# Viewsets setup for logs (list/retrieve) and settings (full CRUD)
api_log_list   = APILogViewSet.as_view({'get': 'list'})
api_log_detail = APILogViewSet.as_view({'get': 'retrieve'})

user_activity_log_list   = UserActivityLogViewSet.as_view({'get': 'list'})
user_activity_log_detail = UserActivityLogViewSet.as_view({'get': 'retrieve'})

system_log_list   = SystemLogViewSet.as_view({'get': 'list'})
system_log_detail = SystemLogViewSet.as_view({'get': 'retrieve'})

settings_list   = SystemSettingsViewSet.as_view({'get': 'list', 'post': 'create'})
settings_detail = SystemSettingsViewSet.as_view({
    'get':    'retrieve',
    'put':    'update',
    'patch':  'partial_update',
    'delete': 'destroy',
})

profiles_list = UserProfileViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
profiles_detail = UserProfileViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    # User / Authentication ----------------------------------------------------
    path('user/signup/', SignupView.as_view(), name='signup'),
    path('user/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('user/resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('user/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('user/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('user/forgot-pin/', ForgotPinView.as_view(), name='forgot-pin'),
    path('user/reset-pin/', ResetPinView.as_view(), name='reset-pin'),
    path('user/login/', LoginView.as_view(), name='login'),
    path('user/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('user/me/', UserProfileView.as_view(), name='me'),
    path('user/profiles/', profiles_list, name='user-profile-list'),
    path('user/profiles/<str:pk>/', profiles_detail, name='user-profile-detail'),

    # Core / System & Logs -----------------------------------------------------
    path('core/health/', HealthCheckView.as_view(), name='health-check'),
    path('core/logs/api/',          api_log_list,   name='api-log-list'),
    path('core/logs/api/<int:pk>/', api_log_detail, name='api-log-detail'),
    path('core/logs/user-activity/',          user_activity_log_list,   name='user-activity-log-list'),
    path('core/logs/user-activity/<int:pk>/', user_activity_log_detail, name='user-activity-log-detail'),
    path('core/logs/system/',          system_log_list,   name='system-log-list'),
    path('core/logs/system/<int:pk>/', system_log_detail, name='system-log-detail'),
    path('core/settings/',          settings_list,   name='system-setting-list'),
    path('core/settings/<int:pk>/', settings_detail, name='system-setting-detail'),
]
