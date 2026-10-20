from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from users.models import CustomUser
from users.serializers import CustomUserSerializer, LoginSerializer, VerifyOTPSerializer, PasswordResetSerializer
import pyotp
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.views.generic import CreateView
from django.urls import reverse_lazy
from users.forms import CustomUserCreationForm, CustomAuthenticationForm, OTPVerificationForm, PractitionerDocumentForm, CompanyDocumentForm, RoleSelectionForm, PractitionerDetailForm, CompanyDetailForm
from users.models import Applicant, Individual, Organization
from users.emails import notify_staff_new_registration, notify_applicant_registration_status
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def system_users_list_view(request):
    is_admin = request.user.is_admin
    if not is_admin:
        return redirect('users:dashboard')
    # Superusers are managed in Django admin only, so they are never listed here.
    staff_users = CustomUser.objects.filter(
        Q(is_staff=True) |
        Q(role__name__in=CustomUser.STAFF_ROLES) |
        Q(additional_roles__name__in=CustomUser.STAFF_ROLES) |
        Q(registration_status='PENDING', is_onboarding_complete=True, role__isnull=True)
    ).exclude(is_superuser=True).distinct().order_by('email')

    return render(request, 'users/system_users_list.html', {'staff_users': staff_users})

@login_required
def system_user_create_view(request):
    is_admin = request.user.is_admin
    if not is_admin:
        return redirect('users:dashboard')
    from users.forms import StaffUserCreationForm
    from users.emails import notify_staff_account_created
    import random
    import string
    if request.method == 'POST':
        form = StaffUserCreationForm(request.POST, request_user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(temp_password)
            user.is_email_verified = False
            user.is_onboarding_complete = True
            user.is_staff = True
            user.registration_status = 'PENDING'
            user.save()
            otp_code = pyotp.TOTP(user.otp_secret).now()
            if settings.DEBUG:  # never write one-time codes to production logs
                print(f'DEBUG: Generated OTP for staff user {user.email} is {otp_code}')
            notify_staff_account_created(user, temp_password, otp_code)
            messages.success(request, f'Successfully created staff user: {user.email}. An email with their temporary password and verification code has been sent.')
            return redirect('users:system_users_list')
    else:
        form = StaffUserCreationForm(request_user=request.user)
    return render(request, 'users/system_user_create.html', {'form': form})

@login_required
def system_user_detail_view(request, pk):
    is_admin = request.user.is_admin
    if not is_admin:
        return redirect('users:dashboard')
    staff_user = get_object_or_404(CustomUser, pk=pk, is_superuser=False)
    return render(request, 'users/system_user_detail.html', {'staff_user': staff_user})

@login_required
def system_user_update_view(request, pk):
    is_admin = request.user.is_admin
    if not is_admin:
        return redirect('users:dashboard')
    user_to_update = get_object_or_404(CustomUser, pk=pk, is_superuser=False)
    from users.forms import StaffUserUpdateForm
    if request.method == 'POST':
        form = StaffUserUpdateForm(request.POST, instance=user_to_update, request_user=request.user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            updated_user.is_staff = True
            updated_user.save()
            form.save_m2m()
            messages.success(request, f'Successfully updated user: {updated_user.email}')
            return redirect('users:system_users_list')
    else:
        form = StaffUserUpdateForm(instance=user_to_update, request_user=request.user)
    return render(request, 'users/system_user_update.html', {'form': form, 'user_to_update': user_to_update})
@login_required
def applicant_users_list_view(request):
    if not request.user.is_staff_member:
        return redirect('users:dashboard')
    
    # Applicants, including people who registered but have not confirmed their email
    # yet (they choose Individual or Company only after the email code).
    applicants = (
        CustomUser.objects.filter(Q(role__name__in=['Individual Applicant', 'Company Applicant']) | Q(role__isnull=True, is_staff=False))
        .exclude(is_superuser=True)
        .exclude(additional_roles__name__in=CustomUser.STAFF_ROLES)
        .distinct()
        .order_by('-date_joined')
    )
    unverified_count = applicants.filter(is_email_verified=False).count()
    status_filter = request.GET.get('status', '')
    if status_filter == 'unverified':
        applicants = applicants.filter(is_email_verified=False)
    
    # Optional filtering
    query = request.GET.get('q', '')
    if query:
        applicants = applicants.filter(
            Q(email__icontains=query) |
            Q(applicant_profile__individual__first_name__icontains=query) |
            Q(applicant_profile__individual__last_name__icontains=query) |
            Q(applicant_profile__organization__organization_name__icontains=query)
        ).distinct()
        
    paginator = Paginator(applicants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/applicant_users_list.html', {
        'applicants': page_obj,
        'query': query,
        'status_filter': status_filter,
        'unverified_count': unverified_count,
        'total_applicants': applicants.count()
    })


def _back_to_list(request):
    from django.utils.http import url_has_allowed_host_and_scheme
    target = request.POST.get('next', '')
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(target)
    return redirect('users:applicant_users_list')


def _unverified_applicant(pk):
    return get_object_or_404(CustomUser, pk=pk, is_superuser=False, is_email_verified=False)


@login_required
def resend_applicant_otp_view(request, pk):
    """Staff send a fresh email code to an applicant who never received one."""
    if request.method != 'POST' or not (request.user.is_admin or request.user.is_evaluator):
        return redirect('users:applicant_users_list')
    from users.emails import send_otp_email
    applicant = _unverified_applicant(pk)
    sent, error = send_otp_email(applicant)
    if sent:
        messages.success(request, f'A new verification code was sent to {applicant.email}. It is valid for 5 minutes; they can also press "Resend code" on the verification page.')
    else:
        messages.error(request, f'The email to {applicant.email} could not be sent: {error}. Check the email settings (EMAIL_HOST, user and password) on the server.')
    return _back_to_list(request)


@login_required
def verify_applicant_email_view(request, pk):
    """An administrator confirms the email address after checking with the person directly."""
    if request.method != 'POST' or not request.user.is_admin:
        return redirect('users:applicant_users_list')
    applicant = _unverified_applicant(pk)
    applicant.is_email_verified = True
    note = f"Email verified manually by {request.user.email} on {timezone.now():%Y-%m-%d %H:%M}."
    applicant.review_remarks = f"{applicant.review_remarks}\n{note}".strip() if applicant.review_remarks else note
    applicant.save(update_fields=['is_email_verified', 'review_remarks'])
    messages.success(request, f'{applicant.email} is now verified and can log in to continue their registration.')
    return _back_to_list(request)

@login_required
def resend_staff_activation_view(request, pk):
    is_admin = request.user.is_admin
    if not is_admin:
        return redirect('users:dashboard')
        
    staff_user = get_object_or_404(CustomUser, pk=pk, is_superuser=False)
    
    # Verify the user is a staff member
    is_staff = staff_user.role and staff_user.role.name in CustomUser.STAFF_ROLES
    if not is_staff:
        messages.error(request, "This action is only available for staff users.")
        return redirect('users:system_users_list')
        
    if staff_user.is_email_verified:
        messages.info(request, f"User {staff_user.email} is already verified and active.")
        return redirect('users:system_users_list')
        
    import random
    import string
    import pyotp
    from users.emails import notify_staff_account_created
    
    # Generate new temporary password
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    staff_user.set_password(temp_password)
    
    # Make sure they have an OTP secret
    if not staff_user.otp_secret:
        staff_user.otp_secret = pyotp.random_base32()
        
    staff_user.save()
    
    # Get current OTP code
    otp_code = pyotp.TOTP(staff_user.otp_secret).now()
    
    # Send email
    notify_staff_account_created(staff_user, temp_password, otp_code)
    
    messages.success(request, f"Successfully reset credentials and sent a new activation email to {staff_user.email}.")
    return redirect('users:system_users_list')
