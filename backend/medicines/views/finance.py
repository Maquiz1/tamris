from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from medicines.forms import MasterMedicineApplicationForm, PreliminaryEvaluationForm, ScientificEvaluationForm, PaymentVerificationForm, ApplicantPaymentSubmissionForm, FeeConfigurationForm, InitiateApplicationForm, InspectionScheduleForm, InspectionReportForm
from django.utils import timezone
from medicines.models import MedicineApplication, MedicineEvaluation, Payment, FeeConfiguration, InspectionSchedule, FeeInactiveError
from django.core.paginator import Paginator
from django.db.models import Q
from medicines import services

@login_required
def staff_payment_list_view(request):
    if not (request.user.is_finance or request.user.is_admin):
        return redirect('users:dashboard')
    base_queryset = Payment.objects.all().order_by('-created_at')
    list_filter = request.GET.get('filter', 'pending')
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if list_filter == 'pending':
        base_queryset = base_queryset.filter(is_verified=False)
    if query:
        base_queryset = base_queryset.filter(Q(application__medicine_name__icontains=query) | Q(application__reference_number__icontains=query) | Q(control_number__icontains=query) | Q(application__applicant__email__icontains=query)).distinct()
    if status_filter == 'VERIFIED':
        base_queryset = base_queryset.filter(is_verified=True)
    elif status_filter == 'PENDING':
        base_queryset = base_queryset.filter(is_verified=False)
    if start_date:
        base_queryset = base_queryset.filter(created_at__date__gte=start_date)
    if end_date:
        base_queryset = base_queryset.filter(created_at__date__lte=end_date)
    paginator = Paginator(base_queryset, 10)
    page_number = request.GET.get('page')
    payments = paginator.get_page(page_number)
    return render(request, 'medicines/staff/payment_list.html', {'payments': payments, 'total_pending': Payment.objects.filter(is_verified=False).count(), 'query': query, 'status_filter': status_filter, 'start_date': start_date, 'end_date': end_date, 'list_filter': list_filter})

@login_required
def staff_payment_detail_view(request, pk):
    if not (request.user.is_finance or request.user.is_admin):
        return redirect('users:dashboard')
    payment = get_object_or_404(Payment, pk=pk)
    application = payment.application
    if request.method == 'POST':
        action = request.POST.get('action')
        remarks = (request.POST.get('remarks') or '').strip()
        try:
            if action == 'mark_paid':
                services.verify_payment(payment, request.user, remarks or None)
                messages.success(request, f'Payment verified for {application.medicine_name}.')
            elif action == 'mark_unpaid':
                services.reject_payment(payment, request.user, remarks)
                messages.warning(request, f'Payment not confirmed for {application.medicine_name}. The applicant has been asked to submit it again.')
        except services.WorkflowError as e:
            messages.error(request, str(e))
            return redirect('medicines:staff_payment_detail', pk=pk)
        return redirect('medicines:staff_payment_list')
    payment_form = PaymentVerificationForm(instance=payment)
    return render(request, 'medicines/staff/payment_detail.html', {'payment': payment, 'application': application, 'payment_form': payment_form})
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

@login_required
def finance_fee_configuration_view(request):
    if not (request.user.is_finance or request.user.is_admin):
        return redirect('users:dashboard')
    from core.utils.fees import FEE_TYPES
    fee_type_order = {code: index for index, (code, _) in enumerate(FEE_TYPES)}
    fee_configs = list(FeeConfiguration.objects.all())
    fee_configs.sort(key=lambda x: fee_type_order.get(x.fee_type, 999))
    if request.method == 'POST':
        fee_type = request.POST.get('fee_type')
        try:
            fee_instance = FeeConfiguration.objects.get(fee_type=fee_type)
        except FeeConfiguration.DoesNotExist:
            fee_instance = None
        form = FeeConfigurationForm(request.POST, instance=fee_instance)
        if form.is_valid():
            fee_obj = form.save(commit=False)
            fee_obj.updated_by = request.user
            fee_obj.save()
            messages.success(request, f'Successfully updated {fee_obj.get_fee_type_display()} to {fee_obj.amount} TZS.')
            return redirect('medicines:finance_fee_configuration')
    else:
        form = FeeConfigurationForm()
    return render(request, 'medicines/staff/fee_configuration.html', {'fee_configs': fee_configs, 'form': form})