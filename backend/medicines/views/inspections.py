from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from medicines.forms import MasterMedicineApplicationForm, PreliminaryEvaluationForm, ScientificEvaluationForm, PaymentVerificationForm, ApplicantPaymentSubmissionForm, FeeConfigurationForm, InitiateApplicationForm, InspectionScheduleForm, InspectionReportForm
from django.utils import timezone
from medicines.models import MedicineApplication, MedicineEvaluation, Payment, FeeConfiguration, InspectionSchedule, FeeInactiveError
from django.core.paginator import Paginator
from django.db.models import Q
from users.emails import notify_inspection_scheduled, notify_evaluators_inspection_report
from medicines import services
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

def awaiting_scheduling():
    """Category II applications whose site inspection still has to be scheduled."""
    return (
        MedicineApplication.objects
        .filter(application_type='CATEGORY_II', status__in=['READY_FOR_INSPECTION', 'PRELIMINARY_APPROVED'], is_legacy=False)
        .exclude(inspections__status='SCHEDULED')
        .distinct()
    )


@login_required
def inspection_dashboard_view(request):
    if not (request.user.is_inspector or request.user.is_admin or request.user.is_evaluator):
        return redirect('users:dashboard')
    unassigned_apps = awaiting_scheduling().order_by('-updated_at')
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
    if not awaiting_scheduling().filter(pk=application.pk).exists():
        messages.error(request, 'An inspection can only be scheduled after preliminary approval and the inspection fee, and when no inspection is already scheduled.')
        return redirect('medicines:inspection_dashboard')
    is_reinspection = application.inspections.filter(status='COMPLETED').exists()
    if request.method == 'POST':
        form = InspectionScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.application = application
            schedule.created_by = request.user
            schedule.save()
            form.save_m2m()
            # Applications approved under the earlier order (schedule first, fee after) get their fee here, once.
            if application.status == 'PRELIMINARY_APPROVED' and not services.has_fee(application, 'inspection'):
                try:
                    services.create_fee(application, 'inspection')
                    application.status = 'PENDING_INSPECTION_FEE'
                    application.save()
                except FeeInactiveError:
                    messages.warning(request, 'Inspection fee configuration is inactive, payment not generated.')
            notify_inspection_scheduled(application, schedule)
            label = 'Re-inspection' if is_reinspection else 'Inspection'
            messages.success(request, f'{label} scheduled for {application.medicine_name}. The applicant and inspectors have been notified.')
            return redirect('medicines:inspection_dashboard')
    else:
        form = InspectionScheduleForm()
    title = 'Schedule Re-inspection' if is_reinspection else 'Schedule Inspection'
    return render(request, 'medicines/staff/inspection_form.html', {'form': form, 'title': title, 'application': application})


@login_required
def submit_inspection_report_view(request, pk):
    if not (request.user.is_inspector or request.user.is_admin):
        return redirect('users:dashboard')
    schedule = get_object_or_404(InspectionSchedule, pk=pk)
    if not request.user.is_admin and request.user not in schedule.assigned_inspectors.all():
        messages.error(request, 'You are not assigned to conduct this inspection.')
        return redirect('medicines:inspection_dashboard')
    if schedule.status != 'SCHEDULED':
        messages.error(request, 'This inspection is not open for a report.')
        return redirect('medicines:inspection_dashboard')

    application = schedule.application
    has_verified_payment = application.payments.filter(payment_type='CAT_II_INSPECTION_FEE', is_verified=True).exists()
    fee_not_paid = not (has_verified_payment or application.status == 'READY_FOR_INSPECTION')

    if has_verified_payment and application.status in ('PENDING_INSPECTION_FEE', 'PRELIMINARY_APPROVED'):
        application.status = 'READY_FOR_INSPECTION'
        application.save()
        fee_not_paid = False

    if request.method == 'POST':
        if fee_not_paid:
            messages.error(request, "Cannot submit report. The inspection fee has not been paid or verified by Finance.")
            return redirect('medicines:inspection_dashboard')
        form = InspectionReportForm(request.POST, request.FILES, instance=schedule)
        if form.is_valid():
            inspection = form.save(commit=False)
            inspection.status = 'COMPLETED'
            inspection.save()
            application.status = 'INSPECTION_COMPLETED'
            application.save()
            notify_evaluators_inspection_report(inspection)
            messages.success(request, f'Inspection report submitted for {application.medicine_name}. Ready for Scientific Evaluation.')
            return redirect('medicines:inspection_dashboard')
    else:
        form = InspectionReportForm(instance=schedule)
    return render(request, 'medicines/staff/inspection_form.html', {
        'form': form,
        'title': 'Submit Inspection Report',
        'application': application,
        'schedule': schedule,
        'fee_not_paid': fee_not_paid,
    })


@login_required
def inspection_detail_view(request, pk):
    """Read-only view of a completed inspection report."""
    if not (request.user.is_inspector or request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    schedule = get_object_or_404(InspectionSchedule, pk=pk)
    # Non-admin inspectors can only view their own assigned inspections
    if request.user.is_inspector and not (request.user.is_admin or request.user.is_evaluator):
        if request.user not in schedule.assigned_inspectors.all():
            messages.error(request, 'You are not assigned to this inspection.')
            return redirect('medicines:inspection_dashboard')
    return render(request, 'medicines/staff/inspection_detail.html', {
        'schedule': schedule,
        'application': schedule.application,
    })