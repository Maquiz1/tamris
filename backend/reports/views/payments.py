from reports.views.utils import is_staff_check, export_csv
import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import models
from django.db.models import Sum, Count, Case, When
from medicines.models import MedicineApplication, Payment, MedicineEvaluation, InspectionSchedule
from users.models import CustomUser

@login_required
@user_passes_test(is_staff_check)
def payments_report_view(request):
    qs = Payment.objects.all().select_related('application').order_by('-created_at')
    
    status_filter = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if status_filter == 'VERIFIED':
        qs = qs.filter(is_verified=True)
    elif status_filter == 'SUBMITTED':
        qs = qs.filter(is_verified=False).exclude(receipt_number__isnull=True).exclude(receipt_number="")
    elif status_filter == 'PENDING':
        qs = qs.filter(is_verified=False).filter(models.Q(receipt_number__isnull=True) | models.Q(receipt_number=""))
        
    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__lte=f"{end_date} 23:59:59")
        
    if request.GET.get('export') == 'csv':
        fields = [{'name': 'id', 'label': 'Receipt ID'}, {'name': 'get_payment_type_display', 'label': 'Fee Type'}, {'name': 'amount', 'label': 'Amount'}, {'name': 'receipt_number', 'label': 'Receipt Number'}, {'name': 'is_verified', 'label': 'Is Verified'}, {'name': 'created_at', 'label': 'Date'}]
        return export_csv(qs, 'payments_report', fields)
        
    # Group by fee type (payment_type)
    fee_summary = Payment.objects.values('payment_type').annotate(
        total_amount=Sum('amount'),
        verified_amount=Sum(Case(
            When(is_verified=True, then='amount'),
            default=0.00,
            output_field=models.DecimalField()
        )),
        pending_amount=Sum(Case(
            When(is_verified=False, then='amount'),
            default=0.00,
            output_field=models.DecimalField()
        )),
        payment_count=Count('id')
    ).order_by('payment_type')
    
    # Process fee summary items to add choice labels
    from core.utils.fees import FEE_TYPES
    payment_type_dict = dict(FEE_TYPES)
    for item in fee_summary:
        item['label'] = payment_type_dict.get(item['payment_type'], item['payment_type'])
        
    # Calculate totals
    total_payment_count = sum(item['payment_count'] for item in fee_summary)
    total_pending_amount = sum(item['pending_amount'] for item in fee_summary)
    total_verified_amount = sum(item['verified_amount'] for item in fee_summary)
    total_all_amount = sum(item['total_amount'] for item in fee_summary)
    
    # Chart Data
    fee_chart_labels = [item['label'] for item in fee_summary]
    fee_chart_data = [float(item['verified_amount']) for item in fee_summary]
    
    verified_count = Payment.objects.filter(is_verified=True).count()
    pending_count = Payment.objects.filter(is_verified=False).exclude(receipt_number__isnull=True).exclude(receipt_number="").count()
    awaiting_count = Payment.objects.filter(is_verified=False).filter(models.Q(receipt_number__isnull=True) | models.Q(receipt_number="")).count()
    
    context = {
        'payments': qs,
        'fee_summary': fee_summary,
        'total_payment_count': total_payment_count,
        'total_pending_amount': total_pending_amount,
        'total_verified_amount': total_verified_amount,
        'total_all_amount': total_all_amount,
        'fee_chart_labels': fee_chart_labels,
        'fee_chart_data': fee_chart_data,
        'verified_count': verified_count,
        'pending_count': pending_count,
        'awaiting_count': awaiting_count,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/payments.html', context)