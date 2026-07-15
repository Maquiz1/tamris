from reports.views.utils import is_staff_check, export_csv
import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import models
from django.db.models import Count
from medicines.models import MedicineApplication, Payment, MedicineEvaluation, InspectionSchedule
from users.models import CustomUser

@login_required
@user_passes_test(is_staff_check)
def applications_report_view(request):
    qs = MedicineApplication.objects.all().select_related('applicant').order_by('-created_at')
    
    # Advanced Filtering
    status_filter = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if status_filter:
        qs = qs.filter(status=status_filter)
    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        # Include the entire end day
        qs = qs.filter(created_at__lte=f"{end_date} 23:59:59")
        
    if request.GET.get('export') == 'csv':
        fields = [{'name': 'id', 'label': 'ID'}, {'name': 'medicine_name', 'label': 'Medicine Name'}, {'name': 'get_application_type_display', 'label': 'Type'}, {'name': 'get_status_display', 'label': 'Status'}, {'name': 'created_at', 'label': 'Date Applied'}]
        return export_csv(qs, 'applications_report', fields)
        
    # Group by status
    status_summary = qs.values('status').annotate(count=Count('id'))
    status_dict = dict(MedicineApplication.STATUS_CHOICES)
    status_labels = [status_dict.get(item['status'], item['status']) for item in status_summary]
    status_data = [item['count'] for item in status_summary]
    
    # Group by application type
    type_summary = qs.values('application_type').annotate(count=Count('id'))
    type_dict = dict(MedicineApplication.APPLICATION_TYPES)
    type_labels = [type_dict.get(item['application_type'], item['application_type']) for item in type_summary]
    type_data = [item['count'] for item in type_summary]
    
    context = {
        'applications': qs,
        'status_labels': status_labels,
        'status_data': status_data,
        'type_labels': type_labels,
        'type_data': type_data,
        # pass context for form:
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'STATUS_CHOICES': MedicineApplication.STATUS_CHOICES,
    }
    return render(request, 'reports/applications.html', context)