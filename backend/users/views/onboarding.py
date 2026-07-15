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
def onboarding_wizard_view(request):
    user = request.user
    if not user.is_email_verified:
        return redirect('users:frontend_verify_otp')
    step = user.onboarding_step
    if step == 5:
        return redirect('users:dashboard')
    context = {'step': step}
    if step == 1:
        context['title'] = 'Step 1: Choose Your Identity'
        context['subtitle'] = 'Select whether you are registering as an individual practitioner or a company.'
        FormClass = RoleSelectionForm
        instance = user
    elif step == 2:
        context['title'] = 'Step 2: Profile Details'
        context['subtitle'] = 'Please provide your identification and registration details.'
        if user.role.name == 'Individual Applicant':
            FormClass = PractitionerDetailForm
            instance = getattr(user, 'user_profile', None)
        else:
            FormClass = CompanyDetailForm
            instance = getattr(user, 'company_profile', None)
    elif step == 3:
        context['title'] = 'Step 3: Document Uploads'
        context['subtitle'] = 'Please upload scanned copies of your mandatory certificates.'
        if user.role.name == 'Individual Applicant':
            FormClass = PractitionerDocumentForm
            instance = user.user_profile
        else:
            FormClass = CompanyDocumentForm
            instance = user.company_profile
    elif step == 4:
        context['title'] = 'Step 4: Review & Submit'
        context['subtitle'] = 'Review your application details. Once submitted, these details will be locked.'
        FormClass = None
        instance = None
    if request.method == 'POST':
        if step == 4:
            user.is_onboarding_complete = True
            user.save()
            notify_staff_new_registration(user)
            messages.success(request, 'Application submitted successfully! Welcome to your dashboard.')
            return redirect('users:dashboard')
        form = FormClass(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            if step == 2:
                obj.user = user
            obj.save()
            return redirect('users:onboarding')
    elif FormClass:
        form = FormClass(instance=instance)
    else:
        form = None
    if form:
        context['form'] = form
    return render(request, 'users/onboarding.html', context)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def reupload_document_view(request):
    if request.method == 'POST':
        doc_key = request.POST.get('doc_key')
        uploaded_file = request.FILES.get('document')
        if not doc_key or not uploaded_file:
            messages.error(request, 'Invalid request. Please select a file.')
            return redirect('users:dashboard')
        user = request.user
        if user.role.name == 'Individual Applicant':
            profile = user.user_profile
        else:
            profile = user.company_profile
        if hasattr(profile, doc_key):
            doc_status = user.document_statuses.get(doc_key, {}).get('status') if user.document_statuses else None
            if doc_status != 'REJECTED':
                messages.error(request, 'You can only re-upload documents that have been rejected.')
                return redirect('users:dashboard')
            setattr(profile, doc_key, uploaded_file)
            profile.save()
            # Update document_statuses dictionary copy to make sure Django detects JSONField change
            statuses = dict(user.document_statuses or {})
            statuses[doc_key] = {'status': 'PENDING', 'reason': ''}
            user.document_statuses = statuses
            has_other_rejections = False
            if user.document_statuses:
                for (key, data) in user.document_statuses.items():
                    if data.get('status') == 'REJECTED':
                        has_other_rejections = True
                        break
            if not has_other_rejections:
                user.registration_status = 'PENDING'
                user.rejection_reason = None
                user.review_remarks = None
            user.save()
            messages.success(request, f'Document successfully re-uploaded. Your application is now pending review.')
        else:
            messages.error(request, 'Invalid document type.')
    return redirect('users:dashboard')