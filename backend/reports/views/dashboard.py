from reports.views.utils import is_staff_check, export_csv
import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import models
from medicines.models import MedicineApplication, Payment, MedicineEvaluation, InspectionSchedule
from users.models import CustomUser

@login_required
@user_passes_test(is_staff_check)
def reports_dashboard_view(request):
    """
    Main dashboard for reports showing high-level metrics.
    """
    status_counts = MedicineApplication.objects.values('status').annotate(count=models.Count('id'))
    status_labels = [item['status'] for item in status_counts]
    status_data = [item['count'] for item in status_counts]
    from datetime import timedelta
    from django.db.models.functions import TruncMonth
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_counts = MedicineApplication.objects.filter(created_at__gte=six_months_ago).annotate(month=TruncMonth('created_at')).values('month').annotate(count=models.Count('id')).order_by('month')
    trend_labels = []
    trend_data = []
    for entry in monthly_counts:
        if entry['month']:
            trend_labels.append(entry['month'].strftime('%b %Y'))
            trend_data.append(entry['count'])
    context = {'total_applications': MedicineApplication.objects.count(), 'total_registered': MedicineApplication.objects.filter(status='FULL_REGISTRATION').count(), 'total_users': CustomUser.objects.count(), 'total_payments_verified': Payment.objects.filter(is_verified=True).count(), 'status_labels': status_labels, 'status_data': status_data, 'trend_labels': trend_labels, 'trend_data': trend_data}
    return render(request, 'reports/dashboard.html', context)