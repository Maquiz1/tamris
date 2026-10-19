from django.db.models import Count
from django.shortcuts import render

from medicines.models import MedicineApplication
from reports.views.utils import report_access, date_range, filter_dates, paginate, as_json, export_csv, visible_applications


@report_access('applications')
def applications_report_view(request):
    qs = visible_applications(MedicineApplication.objects.all()).select_related('applicant').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    source = request.GET.get('source', '')
    start_date, end_date, start_dt, end_dt = date_range(request)

    if status_filter:
        qs = qs.filter(status=status_filter)
    if type_filter:
        qs = qs.filter(application_type=type_filter)
    if source == 'system':
        qs = qs.filter(is_legacy=False)
    elif source == 'legacy':
        qs = qs.filter(is_legacy=True)
    qs = filter_dates(qs, 'created_at', start_dt, end_dt)

    if request.GET.get('export') == 'csv':
        return export_csv(qs, 'applications_report', [
            ('Reference', 'reference_number'),
            ('Medicine Name', 'medicine_name'),
            ('Service', 'get_application_type_display'),
            ('Status', 'display_status'),
            ('Applicant', 'holder_name'),
            ('Applicant Email', lambda a: a.applicant.email),
            ('Phone', lambda a: a.applicant.contact_phone),
            ('Region', lambda a: a.applicant.applicant_region),
            ('Certificate Number', 'certificate_number'),
            ('Started', 'created_at'),
            ('Submitted', 'submitted_at'),
            ('Legacy Entry', 'is_legacy'),
        ])

    status_names = dict(MedicineApplication.STATUS_CHOICES)
    status_summary = qs.values('status').annotate(count=Count('id')).order_by('-count')
    type_names = dict(MedicineApplication.APPLICATION_TYPES)
    type_summary = qs.values('application_type').annotate(count=Count('id')).order_by('application_type')

    page, query_string = paginate(request, qs)
    context = {
        'applications': page,
        'query_string': query_string,
        'total_count': qs.count(),
        'status_labels': as_json([status_names.get(i['status'], i['status']) for i in status_summary]),
        'status_data': as_json([i['count'] for i in status_summary]),
        'type_labels': as_json([type_names.get(i['application_type'], i['application_type']) for i in type_summary]),
        'type_data': as_json([i['count'] for i in type_summary]),
        'status_filter': status_filter,
        'type_filter': type_filter,
        'source': source,
        'start_date': start_date,
        'end_date': end_date,
        'STATUS_CHOICES': MedicineApplication.STATUS_CHOICES,
    }
    return render(request, 'reports/applications.html', context)
