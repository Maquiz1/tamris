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
def staff_registration_list_view(request):
    if not (request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    applications_list = CustomUser.objects.filter(is_onboarding_complete=True, role__name__in=['Individual Applicant', 'Company Applicant']).order_by('-date_joined')
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    list_filter = request.GET.get('filter', 'pending')
    if list_filter == 'pending':
        applications_list = applications_list.filter(registration_status='PENDING')
    if query:
        applications_list = applications_list.filter(Q(email__icontains=query) | Q(user_profile__first_name__icontains=query) | Q(user_profile__last_name__icontains=query) | Q(company_profile__company_name__icontains=query) | Q(nida_number__icontains=query) | Q(brela_number__icontains=query)).distinct()
    if status_filter:
        applications_list = applications_list.filter(registration_status=status_filter)
    if start_date:
        applications_list = applications_list.filter(date_joined__date__gte=start_date)
    if end_date:
        applications_list = applications_list.filter(date_joined__date__lte=end_date)
    paginator = Paginator(applications_list, 5)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)
    return render(request, 'users/staff/registration_list.html', {'applications': applications, 'total_applications': applications_list.count(), 'query': query, 'status_filter': status_filter, 'start_date': start_date, 'end_date': end_date, 'list_filter': list_filter})

@login_required
def staff_registration_detail_view(request, pk):
    if not (request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    application = get_object_or_404(CustomUser, pk=pk, is_onboarding_complete=True)
    return render(request, 'users/staff/registration_detail.html', {'application': application})

@login_required
def staff_registration_action_view(request, pk):
    if not (request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    application = get_object_or_404(CustomUser, pk=pk, is_onboarding_complete=True)
    if request.method == 'POST':
        doc_keys = [key.replace('doc_status_', '') for key in request.POST.keys() if key.startswith('doc_status_')]
        has_rejection = False
        rejection_messages = []
        document_statuses = application.document_statuses or {}
        for key in doc_keys:
            status = request.POST.get(f'doc_status_{key}')
            reason = request.POST.get(f'doc_reason_{key}', '').strip()
            document_statuses[key] = {'status': status, 'reason': reason}
            if status == 'REJECTED':
                has_rejection = True
                human_readable_name = key.replace('_', ' ').title()
                rejection_messages.append(f'{human_readable_name}: {reason}')
        application.document_statuses = document_statuses
        overall_remarks = request.POST.get('overall_remarks', '').strip()
        application.review_remarks = overall_remarks
        if has_rejection:
            application.registration_status = 'REJECTED'
            application.rejection_reason = 'The following documents were rejected:\n' + '\n'.join(rejection_messages)
            messages.warning(request, f'Application for {application.email} has been rejected due to invalid documents.')
            notify_applicant_registration_status(application, 'REJECTED', application.rejection_reason)
        else:
            application.registration_status = 'VERIFIED'
            application.rejection_reason = None
            messages.success(request, f'Application for {application.email} has been fully verified.')
            notify_applicant_registration_status(application, 'VERIFIED')
        application.save()
    return redirect('users:staff_registration_list')