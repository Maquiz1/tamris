from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from medicines.forms import MedicineListingForm, MedicineCategoryIIForm, PreliminaryEvaluationForm, ScientificEvaluationForm, PaymentVerificationForm, ApplicantPaymentSubmissionForm, FeeConfigurationForm, InitiateApplicationForm, InspectionScheduleForm, InspectionReportForm
from django.utils import timezone
from medicines.models import MedicineApplication, MedicineEvaluation, Payment, FeeConfiguration, InspectionSchedule, FeeInactiveError
from django.core.paginator import Paginator
from django.db.models import Q
from users.emails import notify_finance_pending_payment, notify_evaluator_payment_verified, notify_applicant_application_status
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

@login_required
def inspection_dashboard_view(request):
    if not (request.user.is_inspector or request.user.is_admin or request.user.is_evaluator):
        return redirect('users:dashboard')
    unassigned_apps = MedicineApplication.objects.filter(application_type='CATEGORY_II', inspections__isnull=True, status__in=['SUBMITTED', 'UNDER_REVIEW', 'PRELIMINARY_APPROVED']).distinct().order_by('-updated_at')
    if request.user.is_admin or request.user.is_evaluator:
        schedules = InspectionSchedule.objects.filter(status='SCHEDULED').order_by('start_date_time')
        reports = InspectionSchedule.objects.filter(status='COMPLETED').order_by('-updated_at')
        all_inspections = InspectionSchedule.objects.all().order_by('-updated_at')
    else:
        schedules = InspectionSchedule.objects.filter(status='SCHEDULED', assigned_inspectors=request.user).order_by('start_date_time')
        reports = InspectionSchedule.objects.filter(status='COMPLETED', assigned_inspectors=request.user).order_by('-updated_at')
        all_inspections = InspectionSchedule.objects.filter(assigned_inspectors=request.user).order_by('-updated_at')
    return render(request, 'medicines/staff/inspection_dashboard.html', {'unassigned_apps': unassigned_apps, 'schedules': schedules, 'reports': reports, 'all_inspections': all_inspections})

@login_required
def schedule_inspection_view(request, app_id):
    if not (request.user.is_inspector or request.user.is_admin or request.user.is_evaluator):
        return redirect('users:dashboard')
    application = get_object_or_404(MedicineApplication, pk=app_id)
    if request.method == 'POST':
        form = InspectionScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.application = application
            schedule.created_by = request.user
            schedule.save()
            form.save_m2m()
            try:
                inspection_fee = FeeConfiguration.get_fee('CAT_II_INSPECTION_FEE')
                Payment.objects.create(application=application, payment_type='CAT_II_INSPECTION_FEE', amount=inspection_fee)
                application.status = 'PENDING_INSPECTION_FEE'
                application.save()
            except FeeInactiveError:
                messages.warning(request, 'Inspection fee configuration is inactive, payment not generated.')
            from users.emails import notify_inspection_scheduled
            notify_inspection_scheduled(application, schedule)
            messages.success(request, f'Inspection scheduled for {application.medicine_name}. Pending Inspection Fee generation. An email has been sent to the applicant.')
            return redirect('medicines:inspection_dashboard')
    else:
        form = InspectionScheduleForm()
    return render(request, 'medicines/staff/inspection_form.html', {'form': form, 'title': 'Schedule Inspection', 'application': application})

@login_required
def submit_inspection_report_view(request, pk):
    if not (request.user.is_inspector or request.user.is_admin):
        return redirect('users:dashboard')
    schedule = get_object_or_404(InspectionSchedule, pk=pk)
    if not request.user.is_admin and request.user not in schedule.assigned_inspectors.all():
        messages.error(request, 'You are not assigned to conduct this inspection.')
        return redirect('medicines:inspection_dashboard')
    if request.method == 'POST':
        form = InspectionReportForm(request.POST, request.FILES, instance=schedule)
        if form.is_valid():
            inspection = form.save(commit=False)
            if schedule.application.status != 'READY_FOR_INSPECTION':
                messages.error(request, "Cannot submit report. The applicant has not paid the inspection fee or it hasn't been verified by Finance.")
                return redirect('medicines:inspection_dashboard')
            inspection.status = 'COMPLETED'
            inspection.save()
            schedule.application.status = 'INSPECTION_COMPLETED'
            schedule.application.save()
            messages.success(request, f'Inspection report submitted for {schedule.application.medicine_name}. Ready for Scientific Evaluation.')
            return redirect('medicines:inspection_dashboard')
    else:
        form = InspectionReportForm(instance=schedule)
    return render(request, 'medicines/staff/inspection_form.html', {'form': form, 'title': 'Submit Inspection Report', 'application': schedule.application, 'schedule': schedule})