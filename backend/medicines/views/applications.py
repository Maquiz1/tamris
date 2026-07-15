from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from medicines.forms import MedicineListingForm, MedicineCategoryIIForm, PreliminaryEvaluationForm, ScientificEvaluationForm, PaymentVerificationForm, ApplicantPaymentSubmissionForm, FeeConfigurationForm, InitiateApplicationForm, InspectionScheduleForm, InspectionReportForm
from django.utils import timezone
from medicines.models import MedicineApplication, MedicineEvaluation, Payment, FeeConfiguration, InspectionSchedule, FeeInactiveError
from django.core.paginator import Paginator
from django.db.models import Q
from users.emails import notify_finance_pending_payment, notify_evaluator_payment_verified, notify_applicant_application_status

@login_required
def initiate_application_view(request, app_type):
    if request.user.registration_status != 'VERIFIED':
        messages.error(request, 'Your account must be verified before you can apply.')
        return redirect('users:dashboard')
    if app_type not in ['LISTING', 'CATEGORY_II']:
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = InitiateApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            application.application_type = app_type
            application.status = 'PENDING_APPLICATION_FEE'
            application.save()
            try:
                if app_type == 'LISTING':
                    fee_amount = FeeConfiguration.get_fee('LISTING_APP_FEE', 50000.0)
                    payment_code = 'LISTING_APP_FEE'
                else:
                    fee_amount = FeeConfiguration.get_fee('CAT_II_APP_FEE', 100000.0)
                    payment_code = 'CAT_II_APP_FEE'
                Payment.objects.create(application=application, payment_type=payment_code, amount=fee_amount)
                messages.success(request, 'Application initiated. Please submit your Application Fee (Ada ya maombi) receipt.')
                return redirect('users:dashboard')
            except FeeInactiveError as e:
                application.delete()
                messages.error(request, 'New applications are currently suspended because the Application Fee is inactive.')
                return redirect('users:dashboard')
    else:
        form = InitiateApplicationForm()
    try:
        if app_type == 'LISTING':
            fee_amount = FeeConfiguration.get_fee('LISTING_APP_FEE', 0.0)
            fee_obj = FeeConfiguration.objects.get(fee_type='LISTING_APP_FEE')
        else:
            fee_amount = FeeConfiguration.get_fee('CAT_II_APP_FEE', 0.0)
            fee_obj = FeeConfiguration.objects.get(fee_type='CAT_II_APP_FEE')
    except FeeInactiveError:
        messages.error(request, 'New applications are currently suspended. Please try again later.')
        return redirect('users:dashboard')
    return render(request, 'medicines/initiate_application.html', {'app_type': app_type, 'form': form, 'fee_amount': fee_amount, 'fee_obj': fee_obj})

@login_required
def medicine_listing_apply_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if application.status != 'DRAFT':
        messages.error(request, 'Application fee must be verified before filling the form.')
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = MedicineListingForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            app = form.save(commit=False)
            app.status = 'PENDING_EVALUATION_FEE'
            app.submitted_at = timezone.now()
            app.save()
            try:
                Payment.objects.create(application=app, payment_type='LISTING_EVAL_FEE', amount=FeeConfiguration.get_fee('LISTING_EVAL_FEE', 150000.0))
                notify_applicant_application_status(app, 'TAMRIS - Application Submitted Successfully', f'Your medicine listing application has been received.\nPlease submit your Evaluation Fee (Ada ya tathmini) receipt to proceed.')
                messages.success(request, 'Application submitted. Please submit your Evaluation Fee (Ada ya tathmini) receipt.')
                return redirect('users:dashboard')
            except FeeInactiveError:
                app.status = 'DRAFT'
                app.save()
                messages.error(request, 'Cannot submit application because the Evaluation Fee is currently suspended.')
                return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicineListingForm(instance=application)
    return render(request, 'medicines/apply_listing.html', {'form': form, 'application': application})

@login_required
def medicine_category_ii_apply_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if application.status != 'DRAFT':
        messages.error(request, 'Application fee must be verified before filling the form.')
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = MedicineCategoryIIForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            app = form.save(commit=False)
            app.status = 'PENDING_EVALUATION_FEE'
            app.submitted_at = timezone.now()
            app.save()
            try:
                Payment.objects.create(application=app, payment_type='CAT_II_EVAL_FEE', amount=FeeConfiguration.get_fee('CAT_II_EVAL_FEE', 300000.0))
                notify_applicant_application_status(app, 'TAMRIS - Application Submitted Successfully', f'Your medicine category II application has been received.\nPlease submit your Evaluation Fee (Ada ya tathmini) receipt to proceed.')
                messages.success(request, 'Application submitted. Please submit your Evaluation Fee (Ada ya tathmini) receipt.')
                return redirect('users:dashboard')
            except FeeInactiveError:
                app.status = 'DRAFT'
                app.save()
                messages.error(request, 'Cannot submit application because the Evaluation Fee is currently suspended.')
                return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MedicineCategoryIIForm(instance=application)
    return render(request, 'medicines/apply_category_ii.html', {'form': form, 'application': application})

@login_required
def medicine_application_edit_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if application.status != 'CONDITIONS_APPLIED':
        messages.error(request, 'This application is not currently open for edits.')
        return redirect('users:dashboard')
    if application.application_type == 'LISTING':
        form_class = MedicineListingForm
        template_name = 'medicines/apply_listing.html'
    else:
        form_class = MedicineCategoryIIForm
        template_name = 'medicines/apply_category_ii.html'
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=application)
        if form.is_valid():
            app = form.save(commit=False)
            app.status = 'UNDER_REVIEW'
            app.submitted_at = timezone.now()
            app.save()
            messages.success(request, 'Your corrected application has been resubmitted for review.')
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = form_class(instance=application)
    return render(request, template_name, {'form': form, 'is_edit': True})

@login_required
def certificate_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk)
    if not (request.user == application.applicant or request.user.is_staff_member):
        return redirect('users:dashboard')
    if application.status not in ['FULL_REGISTRATION', 'PROVISIONAL_REGISTRATION', 'PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE', 'PENDING_FINAL_APPROVAL']:
        messages.error(request, 'Certificate or Provisional Letter is not yet available for this application.')
        return redirect('users:dashboard')
    return render(request, 'medicines/certificate.html', {'application': application})
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth