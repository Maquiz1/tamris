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
def evaluations_report_view(request):
    qs = MedicineEvaluation.objects.all().select_related('application', 'evaluator').order_by('-created_at')
    
    # Filtering
    docs_filter = request.GET.get('docs_complete')
    quality_filter = request.GET.get('quality_check')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if docs_filter == '1':
        qs = qs.filter(documents_complete=True)
    elif docs_filter == '0':
        qs = qs.filter(documents_complete=False)
    if quality_filter == '1':
        qs = qs.filter(quality_check=True)
    elif quality_filter == '0':
        qs = qs.filter(quality_check=False)
    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__lte=f"{end_date} 23:59:59")
    
    if request.GET.get('export') == 'csv':
        fields = [{'name': lambda e: e.id, 'label': 'Eval ID'}, {'name': lambda e: e.application.medicine_name, 'label': 'Medicine Name'}, {'name': lambda e: e.evaluator.email if e.evaluator else '-', 'label': 'Evaluator'}, {'name': 'documents_complete', 'label': 'Documents Complete'}, {'name': 'quality_check', 'label': 'Quality Checked'}]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'''attachment; filename="evaluations_report_{timezone.now().strftime('%Y%m%d')}.csv"'''
        writer = csv.writer(response)
        writer.writerow([field['label'] for field in fields])
        for obj in qs:
            row = []
            for field in fields:
                if callable(field['name']):
                    row.append(field['name'](obj))
                else:
                    row.append(getattr(obj, field['name'], ''))
            writer.writerow(row)
        return response
        
    docs_complete_count = qs.filter(documents_complete=True).count()
    docs_incomplete_count = qs.filter(documents_complete=False).count()
    quality_checked_count = qs.filter(quality_check=True).count()
    quality_unchecked_count = qs.filter(quality_check=False).count()
    
    context = {
        'evaluations': qs,
        'docs_complete_count': docs_complete_count,
        'docs_incomplete_count': docs_incomplete_count,
        'quality_checked_count': quality_checked_count,
        'quality_unchecked_count': quality_unchecked_count,
        'docs_filter': docs_filter,
        'quality_filter': quality_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/evaluations.html', context)