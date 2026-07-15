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
def inspections_report_view(request):
    qs = InspectionSchedule.objects.all().select_related('application').order_by('-start_date_time')
    
    status_filter = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if status_filter:
        qs = qs.filter(status=status_filter)
    if start_date:
        qs = qs.filter(start_date_time__gte=start_date)
    if end_date:
        qs = qs.filter(start_date_time__lte=f"{end_date} 23:59:59")
        
    if request.GET.get('export') == 'csv':
        fields = [{'name': 'id', 'label': 'Inspection ID'}, {'name': lambda i: i.application.medicine_name, 'label': 'Medicine Name'}, {'name': 'start_date_time', 'label': 'Start Time'}, {'name': 'end_date_time', 'label': 'End Time'}, {'name': 'get_status_display', 'label': 'Status'}]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'''attachment; filename="inspections_report_{timezone.now().strftime('%Y%m%d')}.csv"'''
        writer = csv.writer(response)
        writer.writerow([field['label'] for field in fields])
        for obj in qs:
            row = []
            for field in fields:
                if callable(field['name']):
                    row.append(field['name'](obj))
                else:
                    val = getattr(obj, field['name'], '')
                    if callable(val):
                        val = val()
                    row.append(val)
            writer.writerow(row)
        return response
        
    # Group by status
    status_summary = qs.values('status').annotate(count=models.Count('id'))
    status_dict = dict(InspectionSchedule.STATUS_CHOICES)
    status_labels = [status_dict.get(item['status'], item['status']) for item in status_summary]
    status_data = [item['count'] for item in status_summary]
    
    # Checklist stats
    from django.db.models import Q
    checklist_stats = InspectionSchedule.objects.aggregate(
        manufacturing_area=models.Count('id', filter=Q(check_manufacturing_area=True)),
        machines=models.Count('id', filter=Q(check_machines=True)),
        cleanliness=models.Count('id', filter=Q(check_cleanliness=True)),
        medicine_storage=models.Count('id', filter=Q(check_medicine_storage=True)),
        quality_control=models.Count('id', filter=Q(check_quality_control=True))
    )
    checklist_labels = ['Mfg Area Passes', 'Machine Passes', 'Cleanliness Passes', 'Storage Passes', 'QC System Passes']
    checklist_data = [
        checklist_stats['manufacturing_area'],
        checklist_stats['machines'],
        checklist_stats['cleanliness'],
        checklist_stats['medicine_storage'],
        checklist_stats['quality_control']
    ]
    
    context = {
        'inspections': qs,
        'status_labels': status_labels,
        'status_data': status_data,
        'checklist_labels': checklist_labels,
        'checklist_data': checklist_data,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'STATUS_CHOICES': InspectionSchedule.STATUS_CHOICES,
    }
    return render(request, 'reports/inspections.html', context)