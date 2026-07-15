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
    is_staff_role = request.user.role and request.user.role.name in ['Admin', 'Evaluator', 'Inspector', 'Finance Officer']
    if request.user.onboarding_step < 5 and (not is_staff_role) and (not request.user.is_superuser):
        return redirect('users:onboarding')
    context = {}
    is_superuser = request.user.is_superuser
    role_name = request.user.role.name if request.user.role else None
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
    elif role_name == 'Finance Officer':
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
    return render(request, 'users/profile.html')
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q