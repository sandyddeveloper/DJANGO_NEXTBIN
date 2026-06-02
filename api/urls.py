from django.urls import path

from api.v1.admin.views import (
    PermissionDetailView,
    PermissionListView,
    RoleDetailView,
    RoleListView,
    RolePermissionsView,
    StaffAssignRoleView,
    StaffDetailView,
    StaffListView,
)
from api.v1.core.views import (
    APILogDetailView,
    APILogListView,
    HealthCheckView,
    SystemLogDetailView,
    SystemLogListView,
    SystemSettingsDetailView,
    SystemSettingsListView,
    UserActivityLogDetailView,
    UserActivityLogListView,
)
from api.v1.users.views import (
    ForgotPasswordOrPinView,
    LoginView,
    ResendOTPView,
    ResetPasswordOrPinView,
    SignupView,
    TokenRefreshView,
    UserProfileDetailView,
    UserProfileListView,
    UserProfileView,
    VerifyOTPView,
)

app_name = "v1"

urlpatterns = [
    # User / Authentication ----------------------------------------------------
    path("user/signup/", SignupView.as_view(), name="signup"),
    path("user/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("user/resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("user/forgot-password/", ForgotPasswordOrPinView.as_view(credential_type="password"), name="forgot-password"),
    path("user/reset-password/", ResetPasswordOrPinView.as_view(credential_type="password"), name="reset-password"),
    path("user/forgot-pin/", ForgotPasswordOrPinView.as_view(credential_type="pin"), name="forgot-pin"),
    path("user/reset-pin/", ResetPasswordOrPinView.as_view(credential_type="pin"), name="reset-pin"),
    path("user/login/", LoginView.as_view(), name="login"),
    path("user/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("user/me/", UserProfileView.as_view(), name="me"),
    
    # User Profile CRUD --------------------------------------------------------
    path("user/profiles/", UserProfileListView.as_view(), name="user-profile-list"),
    path("user/profiles/<str:pk>/", UserProfileDetailView.as_view(), name="user-profile-detail"),

    # Core / System & Logs -----------------------------------------------------
    path("core/health/", HealthCheckView.as_view(), name="health-check"),
    path("core/logs/api/", APILogListView.as_view(), name="api-log-list"),
    path("core/logs/api/<int:pk>/", APILogDetailView.as_view(), name="api-log-detail"),
    path("core/logs/user-activity/", UserActivityLogListView.as_view(), name="user-activity-log-list"),
    path("core/logs/user-activity/<int:pk>/", UserActivityLogDetailView.as_view(), name="user-activity-log-detail"),
    path("core/logs/system/", SystemLogListView.as_view(), name="system-log-list"),
    path("core/logs/system/<int:pk>/", SystemLogDetailView.as_view(), name="system-log-detail"),
    path("core/settings/", SystemSettingsListView.as_view(), name="system-setting-list"),
    path("core/settings/<int:pk>/", SystemSettingsDetailView.as_view(), name="system-setting-detail"),

    # Admin / RBAC & Staff -----------------------------------------------------
    path("admin/permissions/", PermissionListView.as_view(), name="admin-permission-list"),
    path("admin/permissions/<int:pk>/", PermissionDetailView.as_view(), name="admin-permission-detail"),
    path("admin/roles/", RoleListView.as_view(), name="admin-role-list"),
    path("admin/roles/<int:pk>/", RoleDetailView.as_view(), name="admin-role-detail"),
    path("admin/roles/<int:pk>/assign-permissions/", RolePermissionsView.as_view(action="assign"), name="admin-role-assign-permissions"),
    path("admin/roles/<int:pk>/remove-permissions/", RolePermissionsView.as_view(action="remove"), name="admin-role-remove-permissions"),
    path("admin/staff/", StaffListView.as_view(), name="admin-staff-list"),
    path("admin/staff/<str:profile_code>/", StaffDetailView.as_view(http_method_names=["get", "patch", "delete"]), name="admin-staff-detail"),
    path("admin/staff/<str:profile_code>/assign-role/", StaffAssignRoleView.as_view(), name="admin-staff-assign-role"),
]
