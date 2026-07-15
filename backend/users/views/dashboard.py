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

@login_required
def dashboard_view(request):
    if not request.user.is_email_verified:
        return redirect('users:frontend_verify_otp')
    if request.user.onboarding_step < 5 and not request.user.is_staff_member:
        return redirect('users:onboarding')
    context = {}
    is_superuser = request.user.is_superuser
    role_name = request.user.role.name if request.user.role else None
    
    # Handle staff users with unassigned roles
    if request.user.is_staff_member and not role_name and not is_superuser:
        return render(request, 'users/dashboards/staff_pending.html')
        
    from medicines.models import MedicineApplication, Payment, InspectionSchedule
    from users.models import CustomUser
    if is_superuser or role_name == 'Admin':
        context['admin_pending_users'] = CustomUser.objects.filter(is_onboarding_complete=True, registration_status='PENDING', role__name__in=['Individual Applicant', 'Company Applicant']).count()
        context['admin_pending_evaluations'] = MedicineApplication.objects.filter(status__in=['UNDER_REVIEW', 'PRELIMINARY_APPROVED', 'INSPECTION_COMPLETED']).count()
        context['admin_pending_inspections'] = InspectionSchedule.objects.filter(status='SCHEDULED').count()
        context['finance_pending_payments'] = Payment.objects.filter(is_verified=False).count()
        return render(request, 'users/dashboards/admin.html', context)
    elif role_name in ['Evaluator', 'Inspector']:
        from medicines.models import InspectionSchedule
        context['eval_pending_prelim'] = MedicineApplication.objects.filter(status='UNDER_REVIEW').count()
        
        # Inspections with assigned inspectors
        context['eval_pending_inspections'] = InspectionSchedule.objects.filter(status='SCHEDULED', assigned_inspectors__isnull=False).distinct().count()
        
        context['eval_pending_sci'] = MedicineApplication.objects.filter(status='PRELIMINARY_APPROVED').count()
        context['eval_pending_final'] = MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').count()
        context['eval_total_listings'] = MedicineApplication.objects.exclude(status='DRAFT').filter(application_type='LISTING').count()
        context['eval_total_cat_ii'] = MedicineApplication.objects.exclude(status='DRAFT').filter(application_type='CATEGORY_II').count()
        context['eval_pending_users'] = CustomUser.objects.filter(is_onboarding_complete=True, registration_status='PENDING', role__name__in=['Individual Applicant', 'Company Applicant']).count()
        context['inspector_pending_assignments'] = MedicineApplication.objects.filter(application_type='CATEGORY_II', inspections__isnull=True, status__in=['SUBMITTED', 'UNDER_REVIEW', 'PRELIMINARY_APPROVED']).distinct().count()
        context['inspector_active_schedules'] = InspectionSchedule.objects.filter(status='SCHEDULED').count()
        context['inspector_completed_reports'] = InspectionSchedule.objects.filter(status='COMPLETED').count()
        return render(request, 'users/dashboards/evaluator.html', context)
    elif role_name == 'Accountant':
        context['finance_pending_payments'] = Payment.objects.filter(is_verified=False).count()
        context['finance_verified_payments'] = Payment.objects.filter(is_verified=True).count()
        return render(request, 'users/dashboards/finance.html', context)
    else:
        context['applicant_inspection_count'] = InspectionSchedule.objects.filter(
            application__applicant=request.user
        ).count()
        return render(request, 'users/dashboards/applicant.html', context)

@login_required
def profile_view(request):
    if not request.user.is_email_verified:
        return redirect('users:frontend_verify_otp')
    if request.user.onboarding_step < 5:
        return redirect('users:onboarding')
        
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    from django.contrib import messages
    
    password_form = PasswordChangeForm(user=request.user)
    show_password_modal = False
    
    if request.method == 'POST' and request.POST.get('action') == 'edit_details':
        if request.user.registration_status != 'REJECTED':
            messages.error(request, "You can only edit your profile details when your registration is rejected.")
            return redirect('users:profile')
            
        phone_number = request.POST.get('phone_number', '').strip()
        user = request.user
        phone_changed = False
        if phone_number and phone_number != user.phone_number:
            user.phone_number = phone_number
            user.is_phone_verified = False  # Reset phone verification!
            phone_changed = True
            
        if 'Individual Applicant' in user.all_roles:
            profile = getattr(user, 'user_profile', None)
            if profile:
                profile.full_name = request.POST.get('full_name', '').strip()
                profile.nida_number = request.POST.get('nida_number', '').strip()
                profile.tin = request.POST.get('tin', '').strip()
                profile.address = request.POST.get('address', '').strip()
                profile.save()
        elif 'Company Applicant' in user.all_roles:
            profile = getattr(user, 'company_profile', None)
            if profile:
                profile.company_name = request.POST.get('company_name', '').strip()
                profile.brela_number = request.POST.get('brela_number', '').strip()
                profile.tin = request.POST.get('tin', '').strip()
                profile.physical_address = request.POST.get('physical_address', '').strip()
                profile.save()
                
        # Check if there are any remaining rejected documents
        has_rejected_docs = False
        if user.document_statuses:
            for (key, data) in user.document_statuses.items():
                if data.get('status') == 'REJECTED':
                    has_rejected_docs = True
                    break
                    
        if not has_rejected_docs:
            user.registration_status = 'PENDING'
            user.rejection_reason = None
            user.review_remarks = None
            
        user.save()
        if phone_changed:
            messages.success(request, 'Profile details updated and resubmitted. Since you changed your phone number, please verify it again.')
        else:
            messages.success(request, 'Profile details successfully updated and resubmitted for review.')
        return redirect('users:profile')

    if request.method == 'POST' and request.POST.get('action') == 'change_password':
        password_form = PasswordChangeForm(user=request.user, data=request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors in the password change form.')
            show_password_modal = True
            
    return render(request, 'users/profile.html', {
        'password_form': password_form,
        'show_password_modal': show_password_modal
    })
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q