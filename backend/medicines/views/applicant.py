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
def applicant_payment_submission_view(request, pk):
    payment = get_object_or_404(Payment, pk=pk, application__applicant=request.user)
    if payment.is_verified:
        messages.error(request, 'This payment is already verified.')
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = ApplicantPaymentSubmissionForm(request.POST, instance=payment)
        if form.is_valid():
            payment_instance = form.save()
            notify_finance_pending_payment(payment_instance, request.user)
            messages.success(request, 'Payment receipt submitted successfully. Waiting for finance verification.')
            return redirect('users:dashboard')
    else:
        form = ApplicantPaymentSubmissionForm(instance=payment)
    return render(request, 'medicines/applicant_payment_submit.html', {'form': form, 'payment': payment})

@login_required
def applicant_payment_list_view(request):
    if not request.user.is_applicant:
        return redirect('users:dashboard')
    payments = Payment.objects.filter(application__applicant=request.user).order_by('-created_at')
    return render(request, 'medicines/applicant_payment_list.html', {'payments': payments})

@login_required
def applicant_certificate_list_view(request):
    if not request.user.is_applicant:
        return redirect('users:dashboard')
    applications = MedicineApplication.objects.filter(applicant=request.user, status__in=['PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION']).order_by('-updated_at')
    return render(request, 'medicines/applicant_certificate_list.html', {'applications': applications})
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

@login_required
def applicant_applications_view(request):
    if not request.user.is_applicant:
        return redirect('users:dashboard')
    applications = list(MedicineApplication.objects.filter(applicant=request.user).prefetch_related('payments').order_by('-created_at'))
    action_required = [app for app in applications if app.requires_applicant_action]
    view_filter = request.GET.get('filter', 'tasks_all')

    def is_payment_task(app):
        if 'PENDING' in app.status and 'FEE' in app.status:
            payments = list(app.payments.all())
            if payments:
                payment = payments[-1]
                if not payment.receipt_number and (not payment.is_verified):
                    return True
        return False
    filtered_action_required = action_required
    filtered_applications = applications
    if view_filter == 'tasks_all':
        pass
    elif view_filter == 'tasks_listing':
        filtered_action_required = [app for app in action_required if not is_payment_task(app) and app.application_type == 'LISTING']
    elif view_filter == 'tasks_cat_ii':
        filtered_action_required = [app for app in action_required if not is_payment_task(app) and app.application_type == 'CATEGORY_II']
    elif view_filter == 'tasks_payment':
        filtered_action_required = [app for app in action_required if is_payment_task(app)]
    elif view_filter == 'apps_all':
        pass
    elif view_filter == 'apps_listing':
        filtered_applications = [app for app in applications if app.application_type == 'LISTING']
    elif view_filter == 'apps_cat_ii':
        filtered_applications = [app for app in applications if app.application_type == 'CATEGORY_II']
    return render(request, 'medicines/applicant/my_applications.html', {'applications': filtered_applications, 'action_required': filtered_action_required, 'view_filter': view_filter})

@login_required
def applicant_listed_medicines_view(request):
    if request.user.role and request.user.role.name != 'Applicant' and (not hasattr(request.user, 'medicine_applications')):
        return redirect('users:dashboard')
    applications = MedicineApplication.objects.filter(applicant=request.user, application_type='LISTING', status__in=['PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION']).order_by('-updated_at')
    return render(request, 'medicines/applicant/approved_medicines.html', {'applications': applications, 'title': 'Listed Medicines', 'icon': 'bi-capsule', 'theme_color': 'success'})

@login_required
def applicant_registered_medicines_view(request):
    if request.user.role and request.user.role.name != 'Applicant' and (not hasattr(request.user, 'medicine_applications')):
        return redirect('users:dashboard')
    applications = MedicineApplication.objects.filter(applicant=request.user, application_type='CATEGORY_II', status__in=['PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION']).order_by('-updated_at')
    return render(request, 'medicines/applicant/approved_medicines.html', {'applications': applications, 'title': 'Registered Medicines', 'icon': 'bi-patch-check', 'theme_color': 'info'})

@login_required
def applicant_application_detail_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk)
    if application.applicant != request.user:
        messages.error(request, 'You do not have permission to view this application.')
        return redirect('users:dashboard')
    return render(request, 'medicines/applicant/application_detail.html', {'application': application})

@login_required
def applicant_reports_view(request):
    if not (request.user.is_applicant or request.user.is_company_applicant):
        return redirect('users:dashboard')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    apps_qs = MedicineApplication.objects.filter(applicant=request.user)
    payments_qs = Payment.objects.filter(application__applicant=request.user)
    if start_date:
        apps_qs = apps_qs.filter(created_at__date__gte=start_date)
        payments_qs = payments_qs.filter(created_at__date__gte=start_date)
    if end_date:
        apps_qs = apps_qs.filter(created_at__date__lte=end_date)
        payments_qs = payments_qs.filter(created_at__date__lte=end_date)
    status_dict = {status[0]: 0 for status in MedicineApplication.STATUS_CHOICES}
    actual_status = apps_qs.values('status').annotate(count=Count('id'))
    for item in actual_status:
        status_dict[item['status']] = item['count']
    sorted_status = sorted(status_dict.items(), key=lambda x: x[1], reverse=True)
    status_labels = [k for (k, v) in sorted_status if v > 0]
    status_data = [status_dict[k] for k in status_labels]
    status_details = [{'label': dict(MedicineApplication.STATUS_CHOICES).get(status, status), 'count': count} for (status, count) in zip(status_labels, status_data)]
    total_amount_paid = payments_qs.filter(is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0.0
    pending_amount = payments_qs.filter(is_verified=False).aggregate(Sum('amount'))['amount__sum'] or 0.0
    context = {'status_labels_json': json.dumps(status_labels, cls=DjangoJSONEncoder), 'status_data_json': json.dumps(status_data, cls=DjangoJSONEncoder), 'status_details': status_details, 'total_applications': apps_qs.count(), 'total_amount_paid': float(total_amount_paid), 'pending_amount': float(pending_amount), 'start_date': start_date, 'end_date': end_date}
    return render(request, 'medicines/applicant/application_report.html', context)