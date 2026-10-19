from django.shortcuts import render

from medicines.models import MedicineEvaluation
from reports.views.utils import report_access, date_range, filter_dates, paginate, export_csv


@report_access('evaluations')
def evaluations_report_view(request):
    qs = (
        MedicineEvaluation.objects.select_related('application', 'evaluator')
        .filter(application__is_void=False, application__is_legacy=False)
        .order_by('-created_at')
    )
    docs_filter = request.GET.get('docs_complete', '')
    quality_filter = request.GET.get('quality_check', '')
    start_date, end_date, start_dt, end_dt = date_range(request)
    if docs_filter in ('0', '1'):
        qs = qs.filter(documents_complete=docs_filter == '1')
    if quality_filter in ('0', '1'):
        qs = qs.filter(quality_check=quality_filter == '1')
    qs = filter_dates(qs, 'created_at', start_dt, end_dt)

    if request.GET.get('export') == 'csv':
        return export_csv(qs, 'evaluations_report', [
            ('Eval ID', 'id'),
            ('Application Reference', lambda e: e.application.reference_number),
            ('Medicine Name', lambda e: e.application.medicine_name),
            ('Service', lambda e: e.application.get_application_type_display()),
            ('Application Status', lambda e: e.application.display_status),
            ('Evaluator', lambda e: e.evaluator.display_name if e.evaluator else ''),
            ('Documents Complete', 'documents_complete'),
            ('Quality', 'quality_check'),
            ('Safety', 'safety_check'),
            ('Efficacy', 'efficacy_check'),
            ('Validity of Tests', 'validity_of_tests'),
            ('Label', 'label_inspection'),
            ('GMP', 'gmp_inspection_check'),
            ('Comments', 'overall_comments'),
            ('Last Updated', 'updated_at'),
        ])

    page, query_string = paginate(request, qs)
    context = {
        'evaluations': page,
        'query_string': query_string,
        'docs_complete_count': qs.filter(documents_complete=True).count(),
        'docs_incomplete_count': qs.filter(documents_complete=False).count(),
        'quality_checked_count': qs.filter(quality_check=True).count(),
        'quality_unchecked_count': qs.filter(quality_check=False).count(),
        'docs_filter': docs_filter,
        'quality_filter': quality_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/evaluations.html', context)
