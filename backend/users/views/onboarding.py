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
from users.forms import CustomUserCreationForm, CustomAuthenticationForm, OTPVerificationForm, PractitionerDocumentForm, CompanyDocumentForm, RoleSelectionForm
from users.forms.profiles import IndividualForm, OrganizationForm, ApplicantIdentityFormSet, ApplicantAddressFormSet, ApplicantContactForm, EducationFormSet, OrganizationRepresentativeFormSet
from users.models import Applicant, Individual, Organization, ApplicantIdentity
from users.emails import notify_staff_new_registration, notify_applicant_registration_status

@login_required
def onboarding_wizard_view(request):
    user = request.user
    if not user.is_email_verified:
        return redirect('users:frontend_verify_otp')
    unlocked_step = user.onboarding_step
    if unlocked_step == 5:
        return redirect('users:profile')
    
    requested_step = request.GET.get('step')
    if requested_step and requested_step.isdigit():
        req_step = int(requested_step)
        if 1 <= req_step <= unlocked_step:
            step = req_step
        else:
            step = unlocked_step
    else:
        step = unlocked_step

    context = {'step': step, 'unlocked_step': unlocked_step}
    if step == 1:
        context['title'] = 'Step 1: Choose Your Identity'
        context['subtitle'] = 'Select whether you are registering as an individual practitioner or a company.'
        FormClass = RoleSelectionForm
        instance = user
    elif step == 2:
        context['title'] = 'Step 2: Profile Details'
        context['subtitle'] = 'Please provide your identification and registration details.'
        applicant, _ = Applicant.objects.get_or_create(
            user=user,
            defaults={'applicant_type': 'Individual' if user.role.name == 'Individual Applicant' else 'Organization'}
        )
        if user.role.name == 'Individual Applicant':
            FormClass = IndividualForm
            instance, _ = Individual.objects.get_or_create(applicant=applicant)
        else:
            FormClass = OrganizationForm
            instance, _ = Organization.objects.get_or_create(
                applicant=applicant,
                defaults={'organization_name': f'Temp Org {applicant.id}', 'registration_number': f'TEMP-{applicant.id}'}
            )
    elif step == 3:
        context['title'] = 'Step 3: Document Uploads'
        context['subtitle'] = 'Please upload scanned copies of your mandatory certificates.'
        if user.role.name == 'Individual Applicant':
            FormClass = PractitionerDocumentForm
            instance = user.applicant_profile
        else:
            FormClass = CompanyDocumentForm
            instance = user.applicant_profile
    elif step == 4:
        context['title'] = 'Step 4: Review & Submit'
        context['subtitle'] = 'Review your application details. Once submitted, these details will be locked.'
        FormClass = None
        instance = None
    if request.method == 'POST':
        # Handle inline role-change from the step-2 type selector
        if request.POST.get('change_role'):
            from users.models import Role
            new_role_name = request.POST.get('change_role')
            try:
                new_role = Role.objects.get(name=new_role_name)
                user.role = new_role
                # Delete any existing profile so step progresses correctly
                if hasattr(user, 'applicant_profile'):
                    user.applicant_profile.hard_delete()
                user.save()
            except Role.DoesNotExist:
                pass
            return redirect('users:onboarding')
        if step == 4:
            user.is_onboarding_complete = True
            user.save()
            notify_staff_new_registration(user)
            messages.success(request, 'Application submitted successfully! Welcome to your dashboard.')
            return redirect('users:dashboard')
        is_draft = bool(request.POST.get('save_draft'))
        
        formset = None
        address_formset = None
        contact_formset = None
        education_formset = None
        rep_formset = None
        if step == 2:
            form = FormClass(request.POST, request.FILES, instance=instance)
            address_formset = ApplicantAddressFormSet(request.POST, instance=instance.applicant)
            contact_formset = ApplicantContactForm(request.POST, instance=getattr(instance.applicant, 'contact', None), prefix='contact')
            if user.role.name == 'Individual Applicant':
                id_qs = ApplicantIdentity.objects.filter(
                    id__in=ApplicantIdentity.objects.filter(applicant=instance.applicant).order_by('id').values('id')[:1]
                )
                formset = ApplicantIdentityFormSet(request.POST, instance=instance.applicant, queryset=id_qs)
                education_formset = EducationFormSet(request.POST, instance=instance.applicant)
            else:
                rep_formset = OrganizationRepresentativeFormSet(request.POST, instance=instance)
        else:
            form = FormClass(request.POST, request.FILES, instance=instance)
            
        if is_draft:
            for f in form.fields.values():
                f.required = False
            for fset in [formset, address_formset, education_formset, rep_formset]:
                if fset:
                    for fset_form in fset.forms:
                        for f in fset_form.fields.values():
                            f.required = False
            if contact_formset:
                for f in contact_formset.fields.values():
                    f.required = False

        if form.is_valid() and (not contact_formset or contact_formset.is_valid()):
            all_formsets_valid = True
            for fset in [formset, address_formset, education_formset, rep_formset]:
                if fset and not fset.is_valid():
                    all_formsets_valid = False
                    messages.error(request, f"Formset error: {fset.errors} {fset.non_form_errors()}")
                
            if all_formsets_valid:
                saved_instance = form.save()
                if contact_formset:
                    contact_instance = contact_formset.save(commit=False)
                    contact_instance.applicant = instance.applicant
                    contact_instance.save()
                for fset in [formset, address_formset, education_formset]:
                    if fset:
                        fset.instance = instance.applicant
                        fset.save()
                if rep_formset:
                    rep_formset.instance = instance
                    rep_formset.save()
                    
                # The onboarding_step is calculated dynamically based on profile completeness.
                # Just save the user to ensure any other updates are persisted.
                user.save()

                if is_draft:
                    messages.success(request, 'Draft saved successfully!')
                else:
                    messages.success(request, 'Information saved successfully!')
                return redirect('users:onboarding')
            else:
                context['formset'] = formset
                context['address_formset'] = address_formset
                context['contact_formset'] = contact_formset
                context['education_formset'] = education_formset
                context['rep_formset'] = rep_formset
        else:
            if not form.is_valid():
                messages.error(request, f"Form error: {form.errors}")
            if contact_formset and not contact_formset.is_valid():
                messages.error(request, f"Contact Form error: {contact_formset.errors}")
            context['formset'] = formset
            context['address_formset'] = address_formset
            context['contact_formset'] = contact_formset
            context['education_formset'] = education_formset
            context['rep_formset'] = rep_formset
    elif FormClass:
        formset = None
        address_formset = None
        contact_formset = None
        education_formset = None
        rep_formset = None
        if step == 2:
            form = FormClass(instance=instance)
            address_formset = ApplicantAddressFormSet(instance=instance.applicant)
            contact_formset = ApplicantContactForm(
                instance=getattr(instance.applicant, 'contact', None), 
                initial={'email': request.user.email},
                prefix='contact'
            )
            if user.role.name == 'Individual Applicant':
                id_qs = ApplicantIdentity.objects.filter(
                    id__in=ApplicantIdentity.objects.filter(applicant=instance.applicant).order_by('id').values('id')[:1]
                )
                formset = ApplicantIdentityFormSet(instance=instance.applicant, queryset=id_qs)
                education_formset = EducationFormSet(instance=instance.applicant)
            else:
                rep_formset = OrganizationRepresentativeFormSet(instance=instance)
        else:
            form = FormClass(instance=instance)
    else:
        form = None
        formset = None
        address_formset = None
        contact_formset = None
        education_formset = None
        rep_formset = None
        
    if form:
        context['form'] = form
    if formset:
        context['formset'] = formset
    if address_formset:
        context['address_formset'] = address_formset
    if contact_formset:
        context['contact_formset'] = contact_formset
    if education_formset:
        context['education_formset'] = education_formset
    if rep_formset:
        context['rep_formset'] = rep_formset
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
        if not hasattr(user, 'applicant_profile'):
            messages.error(request, 'Applicant profile not found.')
            return redirect('users:dashboard')
            
        applicant = user.applicant_profile
        doc_status = user.document_statuses.get(doc_key, {}).get('status') if user.document_statuses else None
        doc_exists = applicant.documents.filter(document_type=doc_key).exists()
        
        # Allow upload if document was rejected OR if it's completely missing
        if doc_status != 'REJECTED' and doc_exists:
            messages.error(request, 'You can only re-upload documents that have been rejected.')
            return redirect('users:dashboard')
            
        from users.models.profiles import ApplicantDocument
        ApplicantDocument.objects.update_or_create(
            applicant=applicant,
            document_type=doc_key,
            defaults={'file': uploaded_file}
        )
        
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
        messages.success(request, f'Document successfully uploaded. Your application is now pending review.')
        
    return redirect('users:dashboard')