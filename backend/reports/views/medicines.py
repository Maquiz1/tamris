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
def medicines_report_view(request):
    qs = MedicineApplication.objects.filter(status__in=['FULL_REGISTRATION', 'PROVISIONAL_REGISTRATION']).order_by('-updated_at')
    
    app_type = request.GET.get('type')
    status_filter = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if app_type:
        qs = qs.filter(application_type=app_type)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if start_date:
        qs = qs.filter(updated_at__gte=start_date)
    if end_date:
        qs = qs.filter(updated_at__lte=f"{end_date} 23:59:59")
        
    if request.GET.get('export') == 'csv':
        fields = [{'name': 'registration_number', 'label': 'Registration Number'}, {'name': 'medicine_name', 'label': 'Medicine Name'}, {'name': 'get_application_type_display', 'label': 'Type'}, {'name': 'get_status_display', 'label': 'Registration Level'}, {'name': 'updated_at', 'label': 'Approval Date'}]
        return export_csv(qs, 'medicines_report', fields)
        
    full_count = qs.filter(status='FULL_REGISTRATION').count()
    provisional_count = qs.filter(status='PROVISIONAL_REGISTRATION').count()
    context = {
        'medicines': qs,
        'full_count': full_count,
        'provisional_count': provisional_count,
        'app_type': app_type,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/medicines.html', context)