from django.urls import path
from django.views.generic.base import RedirectView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, VerifyOTPView, PasswordResetRequestView,
    FrontendRegisterView, frontend_login_view, frontend_logout_view,
    verify_otp_view, dashboard_view, onboarding_wizard_view, profile_view,
    staff_registration_list_view, staff_registration_detail_view, staff_registration_action_view,
    reupload_document_view, system_users_list_view, system_user_create_view,
    system_user_update_view, system_user_detail_view, applicant_users_list_view,
    send_phone_otp_view, verify_phone_otp_view, resend_email_otp_view
)

app_name = 'users'

urlpatterns = [
    # API endpoints
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('api/login/', LoginView.as_view(), name='api_login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/verify-otp/', VerifyOTPView.as_view(), name='api_verify_otp'),
    path('api/password-reset/', PasswordResetRequestView.as_view(), name='api_password_reset'),

    # Frontend template URLs
    path('', RedirectView.as_view(pattern_name='users:frontend_login'), name='root'),
    path('register/', FrontendRegisterView.as_view(), name='frontend_register'),
    path('login/', frontend_login_view, name='frontend_login'),
    path('logout/', frontend_logout_view, name='frontend_logout'),
    path('verify-otp/', verify_otp_view, name='frontend_verify_otp'),
    path('verify-otp/resend/', resend_email_otp_view, name='resend_email_otp'),
    path('onboarding/', onboarding_wizard_view, name='onboarding'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('profile/send-phone-otp/', send_phone_otp_view, name='send_phone_otp'),
    path('profile/verify-phone-otp/', verify_phone_otp_view, name='verify_phone_otp'),
    
    # Staff / Evaluator URLs for Registration Verification
    path('staff/registrations/', staff_registration_list_view, name='staff_registration_list'),
    path('staff/registrations/<int:pk>/', staff_registration_detail_view, name='staff_registration_detail'),
    path('staff/registrations/<int:pk>/action/', staff_registration_action_view, name='staff_registration_action'),
    path('applicants/', applicant_users_list_view, name='applicant_users_list'),
    path('system-users/', system_users_list_view, name='system_users_list'),
    path('system-users/create/', system_user_create_view, name='system_user_create'),
    path('system-users/<int:pk>/', system_user_detail_view, name='system_user_detail'),
    path('system-users/<int:pk>/edit/', system_user_update_view, name='system_user_update'),
    path('reupload-document/', reupload_document_view, name='reupload_document'),
]
