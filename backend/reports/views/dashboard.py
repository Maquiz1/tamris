import datetime

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from medicines.models import MedicineApplication, Payment
from users.models import CustomUser
from reports.views.utils import report_access, as_json, visible_applications, REPORT_ACCESS


@report_access('dashboard')
def reports_dashboard_view(request):
    """Main dashboard for reports showing high-level metrics."""
    applications = visible_applications(MedicineApplication.objects.all())
    status_names = dict(MedicineApplication.STATUS_CHOICES)
    status_counts = applications.values('status').annotate(count=Count('id')).order_by('-count')

    six_months_ago = timezone.now() - datetime.timedelta(days=180)
    monthly_counts = (
        applications.filter(created_at__gte=six_months_ago, is_legacy=False)
        .annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
    )
    today = timezone.localdate()
    certified = applications.filter(status='FULL_REGISTRATION', certificate_expires_on__isnull=False)
    user = request.user
    context = {
        'can': {name: user.is_superuser or check(user) for name, check in REPORT_ACCESS.items()},
        'total_applications': applications.filter(is_legacy=False).count(),
        'total_registered': certified.filter(certificate_expires_on__gte=today).count(),
        'total_users': CustomUser.objects.exclude(is_superuser=True).count(),
        'total_payments_verified': Payment.objects.filter(is_verified=True, paid_before_system=False).count(),
        'expiring_soon': certified.filter(certificate_expires_on__gte=today, certificate_expires_on__lte=today + datetime.timedelta(days=90)).count(),
        'expired': certified.filter(certificate_expires_on__lt=today).count(),
        'status_labels': as_json([status_names.get(i['status'], i['status']) for i in status_counts]),
        'status_data': as_json([i['count'] for i in status_counts]),
        'trend_labels': as_json([i['month'].strftime('%b %Y') for i in monthly_counts if i['month']]),
        'trend_data': as_json([i['count'] for i in monthly_counts if i['month']]),
    }
    return render(request, 'reports/dashboard.html', context)
