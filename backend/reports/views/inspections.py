from django.db.models import Count, Q
from django.shortcuts import render

from medicines.models import InspectionSchedule
from reports.views.utils import report_access, date_range, filter_dates, paginate, as_json, export_csv


def inspector_names(inspection):
    return ', '.join(i.display_name for i in inspection.assigned_inspectors.all())


@report_access('inspections')
def inspections_report_view(request):
    qs = InspectionSchedule.objects.select_related('application', 'application__applicant').prefetch_related('assigned_inspectors').order_by('-start_date_time')
    status_filter = request.GET.get('status', '')
    result_filter = request.GET.get('result', '')
    start_date, end_date, start_dt, end_dt = date_range(request)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if result_filter == 'compliant':
        qs = qs.filter(status='COMPLETED', gmp_compliant=True)
    elif result_filter == 'not_compliant':
        qs = qs.filter(status='COMPLETED', gmp_compliant=False)
    qs = filter_dates(qs, 'start_date_time', start_dt, end_dt)

    if request.GET.get('export') == 'csv':
        return export_csv(qs, 'inspections_report', [
            ('Inspection ID', 'id'),
            ('Application Reference', lambda i: i.application.reference_number),
            ('Medicine Name', lambda i: i.application.medicine_name),
            ('Applicant', lambda i: i.application.holder_name),
            ('Region', lambda i: i.application.applicant.applicant_region),
            ('Inspectors', inspector_names),
            ('Start', 'start_date_time'),
            ('End', 'end_date_time'),
            ('Status', 'get_status_display'),
            ('GMP Compliant', lambda i: (('Yes' if i.gmp_compliant else 'No') if i.status == 'COMPLETED' else '')),
            ('Manufacturing Area', 'manufacturing_area_remarks'),
            ('Machines', 'machines_remarks'),
            ('Cleanliness', 'cleanliness_remarks'),
            ('Medicine Storage', 'medicine_storage_remarks'),
            ('Quality Control', 'quality_control_remarks'),
            ('Inspector Remarks', 'remarks'),
        ])

    status_names = dict(InspectionSchedule.STATUS_CHOICES)
    status_summary = qs.values('status').annotate(count=Count('id'))
    completed = qs.filter(status='COMPLETED')
    outcome = completed.aggregate(
        compliant=Count('id', filter=Q(gmp_compliant=True)),
        not_compliant=Count('id', filter=Q(gmp_compliant=False)),
    )
    # Applications inspected more than once are re-inspections
    reinspections = (
        completed.values('application').annotate(n=Count('id')).filter(n__gt=1).count()
    )
    # Items the evaluator asked inspectors to look at (not results)
    checklist = qs.aggregate(
        manufacturing_area=Count('id', filter=Q(check_manufacturing_area=True)),
        machines=Count('id', filter=Q(check_machines=True)),
        cleanliness=Count('id', filter=Q(check_cleanliness=True)),
        medicine_storage=Count('id', filter=Q(check_medicine_storage=True)),
        quality_control=Count('id', filter=Q(check_quality_control=True)),
    )

    page, query_string = paginate(request, qs)
    context = {
        'inspections': page,
        'query_string': query_string,
        'status_labels': as_json([status_names.get(i['status'], i['status']) for i in status_summary]),
        'status_data': as_json([i['count'] for i in status_summary]),
        'outcome_labels': as_json(['GMP compliant', 'Not compliant']),
        'outcome_data': as_json([outcome['compliant'], outcome['not_compliant']]),
        'compliant_count': outcome['compliant'],
        'not_compliant_count': outcome['not_compliant'],
        'reinspection_count': reinspections,
        'checklist_labels': as_json(['Manufacturing area', 'Machines', 'Cleanliness', 'Medicine storage', 'Quality control']),
        'checklist_data': as_json([checklist['manufacturing_area'], checklist['machines'], checklist['cleanliness'], checklist['medicine_storage'], checklist['quality_control']]),
        'status_filter': status_filter,
        'result_filter': result_filter,
        'start_date': start_date,
        'end_date': end_date,
        'STATUS_CHOICES': InspectionSchedule.STATUS_CHOICES,
    }
    return render(request, 'reports/inspections.html', context)
