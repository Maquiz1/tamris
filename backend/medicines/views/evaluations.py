from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from medicines.forms import MedicineListingForm, MedicineCategoryIIForm, PreliminaryEvaluationForm, ScientificEvaluationForm, PaymentVerificationForm, ApplicantPaymentSubmissionForm, FeeConfigurationForm, InitiateApplicationForm, InspectionScheduleForm, InspectionReportForm
from django.utils import timezone
from medicines.models import MedicineApplication, MedicineEvaluation, Payment, FeeConfiguration, InspectionSchedule, FeeInactiveError
from django.core.paginator import Paginator
from django.db.models import Q
from users.emails import notify_finance_pending_payment, notify_evaluator_payment_verified, notify_applicant_application_status
from medicines.views.utils import get_filtered_applications

@login_required
def staff_preliminary_list_view(request):
    if not (request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    list_filter = request.GET.get('filter', 'pending')
    if list_filter == 'pending':
        base_qs = MedicineApplication.objects.filter(status='UNDER_REVIEW').order_by('-submitted_at')
    else:
        base_qs = MedicineApplication.objects.exclude(status__in=['DRAFT', 'PENDING_APPLICATION_FEE', 'PENDING_EVALUATION_FEE']).order_by('-submitted_at')
    (applications_list, query, status_filter, start_date, end_date) = get_filtered_applications(request, base_qs)
    paginator = Paginator(applications_list, 10)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)
    return render(request, 'medicines/staff/preliminary_list.html', {'applications': applications, 'total_applications': applications_list.count(), 'query': query, 'status_filter': status_filter, 'start_date': start_date, 'end_date': end_date, 'list_filter': list_filter})

@login_required
def staff_preliminary_detail_view(request, pk):
    if not (request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    application = get_object_or_404(MedicineApplication, pk=pk)
    (evaluation, created) = MedicineEvaluation.objects.get_or_create(application=application)
    if request.method == 'POST':
        action = request.POST.get('action')
        evaluation_form = PreliminaryEvaluationForm(request.POST, instance=evaluation)
        if evaluation_form.is_valid():
            eval_instance = evaluation_form.save(commit=False)
            eval_instance.evaluator = request.user
            eval_instance.save()
            if action == 'approve':
                application.status = 'PRELIMINARY_APPROVED'
                messages.success(request, f'Application for {application.medicine_name} passed preliminary screening.')
                notify_applicant_application_status(application, 'TAMRIS - Preliminary Screening Passed', 'Your application has passed the preliminary screening. It is now queued for Scientific Evaluation.')
            elif action == 'reject':
                application.status = 'REJECTED'
                application.rejection_reason = 'Failed preliminary screening.'
                messages.error(request, f'Application for {application.medicine_name} rejected at preliminary screening.')
                notify_applicant_application_status(application, 'TAMRIS - Application Rejected', 'Your application has been rejected at the preliminary screening stage.')
            application.save()
            return redirect('medicines:staff_preliminary_list')
    else:
        evaluation_form = PreliminaryEvaluationForm(instance=evaluation)
    return render(request, 'medicines/staff/preliminary_detail.html', {'application': application, 'evaluation_form': evaluation_form})

@login_required
def staff_scientific_list_view(request):
    if not (request.user.is_evaluator or request.user.is_admin or request.user.is_inspector):
        return redirect('users:dashboard')
    list_filter = request.GET.get('filter', 'pending')
    if list_filter == 'pending':
        base_qs = MedicineApplication.objects.filter(status__in=['PRELIMINARY_APPROVED', 'INSPECTION_COMPLETED']).order_by('-submitted_at')
    elif list_filter == 'final':
        base_qs = MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').order_by('-submitted_at')
    elif list_filter == 'approved':
        base_qs = MedicineApplication.objects.filter(status__in=['PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION']).order_by('-submitted_at')
    else:
        base_qs = MedicineApplication.objects.filter(status__in=['PRELIMINARY_APPROVED', 'INSPECTION_COMPLETED', 'PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE', 'PENDING_FINAL_APPROVAL', 'PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION', 'CONDITIONS_APPLIED', 'REJECTED']).order_by('-submitted_at')
    (applications_list, query, status_filter, start_date, end_date) = get_filtered_applications(request, base_qs)
    paginator = Paginator(applications_list, 10)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)
    return render(request, 'medicines/staff/scientific_list.html', {'applications': applications, 'total_applications': applications_list.count(), 'query': query, 'status_filter': status_filter, 'start_date': start_date, 'end_date': end_date, 'list_filter': list_filter})

@login_required
def staff_scientific_detail_view(request, pk):
    if not (request.user.is_evaluator or request.user.is_admin or request.user.is_inspector):
        return redirect('users:dashboard')
    application = get_object_or_404(MedicineApplication, pk=pk)
    (evaluation, created) = MedicineEvaluation.objects.get_or_create(application=application)
    if request.method == 'POST':
        if request.user.is_inspector and not (request.user.is_evaluator or request.user.is_admin):
            messages.error(request, "Inspectors cannot perform evaluation actions.")
            return redirect('medicines:staff_scientific_list')
        
        action = request.POST.get('action')
        evaluation_form = ScientificEvaluationForm(request.POST, instance=evaluation)
        if evaluation_form.is_valid():
            eval_instance = evaluation_form.save(commit=False)
            eval_instance.evaluator = request.user
            eval_instance.save()
            if action == 'provisional':
                if application.application_type == 'CATEGORY_II':
                    application.status = 'PENDING_REGISTRATION_FEE'
                    payment_type = 'CAT_II_REGISTRATION_FEE'
                    fee_name = 'Registration Fee'
                else:
                    application.status = 'PENDING_LISTING_FEE'
                    payment_type = 'LISTING_FEE'
                    fee_name = 'Listing Fee'
                try:
                    Payment.objects.create(application=application, payment_type=payment_type, amount=FeeConfiguration.get_fee(payment_type, 200000.0))
                    messages.success(request, f'Provisional Registration approved! {fee_name} generated for {application.medicine_name}.')
                    notify_applicant_application_status(application, 'TAMRIS - Provisional Registration Approved', f'Your application has been provisionally approved.\nPlease log in to the TAMRIS portal and submit your {fee_name} receipt to proceed to Full Registration.')
                except FeeInactiveError:
                    messages.error(request, f'Cannot approve provisional registration because the {fee_name} is currently suspended.')
                    return redirect('medicines:staff_scientific_list')
            elif action == 'full':
                application.status = 'FULL_REGISTRATION'
                messages.success(request, f'Full Registration Certificate issued for {application.medicine_name}!')
                notify_applicant_application_status(application, 'TAMRIS - Full Registration Granted', 'Congratulations! Your medicine application has been granted Full Registration.\nYou can now download your certificate from the TAMRIS portal.')
            elif action == 'reject':
                application.status = 'REJECTED'
                application.rejection_reason = eval_instance.overall_comments
                messages.error(request, f'Application for {application.medicine_name} has been rejected.')
                notify_applicant_application_status(application, 'TAMRIS - Application Rejected', f'Unfortunately, your application for {application.medicine_name} has been rejected after Scientific Evaluation.\nReason: {eval_instance.overall_comments}')
            elif action == 'under_review':
                application.status = 'UNDER_REVIEW'
                messages.info(request, f'Application for {application.medicine_name} is marked as Under Review.')
            application.save()
            return redirect('medicines:staff_scientific_list')
    else:
        evaluation_form = ScientificEvaluationForm(instance=evaluation)
    return render(request, 'medicines/staff/scientific_detail.html', {'application': application, 'evaluation_form': evaluation_form})
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth