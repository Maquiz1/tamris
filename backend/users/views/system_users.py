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
from django.views.generic import CreateView
from django.urls import reverse_lazy
from users.forms import CustomUserCreationForm, CustomAuthenticationForm, OTPVerificationForm, PractitionerDocumentForm, CompanyDocumentForm, RoleSelectionForm, PractitionerDetailForm, CompanyDetailForm
from users.models import UserProfile, CompanyProfile
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
    staff_users = CustomUser.objects.filter(
        Q(is_staff=True) |
        Q(is_superuser=True) |
        Q(role__name__in=['Evaluator', 'Inspector', 'Finance Officer', 'Admin']) |
        Q(additional_roles__name__in=['Evaluator', 'Inspector', 'Finance Officer', 'Admin']) |
        Q(registration_status='PENDING', is_onboarding_complete=True, role__isnull=True)
    ).distinct().order_by('email')

    if not request.user.is_superuser:
        staff_users = staff_users.exclude(is_superuser=True)

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
    staff_user = get_object_or_404(CustomUser, pk=pk)
    return render(request, 'users/system_user_detail.html', {'staff_user': staff_user})

@login_required
def system_user_update_view(request, pk):
    is_admin = request.user.is_admin
    if not is_admin:
        return redirect('users:dashboard')
    user_to_update = get_object_or_404(CustomUser, pk=pk)
    if user_to_update.is_superuser and (not request.user.is_superuser):
        messages.error(request, 'You do not have permission to edit this superuser.')
        return redirect('users:system_users_list')
    from users.forms import StaffUserUpdateForm
    if request.method == 'POST':
        form = StaffUserUpdateForm(request.POST, instance=user_to_update, request_user=request.user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            updated_user.is_staff = True
            if updated_user.is_admin and request.user.is_superuser:
                updated_user.is_superuser = True
            elif not updated_user.is_admin:
                updated_user.is_superuser = False
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
    
    applicants = CustomUser.objects.filter(role__name__in=['Individual Applicant', 'Company Applicant']).order_by('-date_joined')
    
    # Optional filtering
    query = request.GET.get('q', '')
    if query:
        applicants = applicants.filter(
            Q(email__icontains=query) |
            Q(user_profile__full_name__icontains=query) |
            Q(company_profile__company_name__icontains=query)
        ).distinct()
        
    paginator = Paginator(applicants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/applicant_users_list.html', {
        'applicants': page_obj,
        'query': query,
        'total_applicants': applicants.count()
    })

@login_required
def resend_staff_activation_view(request, pk):
    is_admin = request.user.is_admin
    if not is_admin:
        return redirect('users:dashboard')
        
    staff_user = get_object_or_404(CustomUser, pk=pk)
    
    # Verify the user is a staff member
    is_staff = staff_user.role and staff_user.role.name in ['Admin', 'Evaluator', 'Inspector', 'Finance Officer']
    if not (is_staff or staff_user.is_superuser):
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
