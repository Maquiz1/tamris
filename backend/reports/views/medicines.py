from django.shortcuts import render
from django.utils import timezone

from medicines.models import MedicineApplication
from reports.views.utils import report_access, date_range, filter_dates, paginate, export_csv, visible_applications


@report_access('medicines')
def medicines_report_view(request):
    """The register: every listed or registered medicine with a certificate."""
    today = timezone.localdate()
    qs = (
        visible_applications(MedicineApplication.objects.filter(status='FULL_REGISTRATION'))
        .exclude(certificate_number__isnull=True)
        .select_related('applicant')
        .order_by('-certificate_issued_on', '-updated_at')
    )
    app_type = request.GET.get('type', '')
    validity = request.GET.get('status', '')
    source = request.GET.get('source', '')
    start_date, end_date, start_dt, end_dt = date_range(request)

    if app_type:
        qs = qs.filter(application_type=app_type)
    if source == 'legacy':
        qs = qs.filter(is_legacy=True)
    elif source == 'system':
        qs = qs.filter(is_legacy=False)
    if start_date:
        qs = qs.filter(certificate_issued_on__gte=start_date)
    if end_date:
        qs = qs.filter(certificate_issued_on__lte=end_date)
    valid_count = qs.filter(certificate_expires_on__gte=today).count()
    expired_count = qs.filter(certificate_expires_on__lt=today).count()
    if validity == 'VALID':
        qs = qs.filter(certificate_expires_on__gte=today)
    elif validity == 'EXPIRED':
        qs = qs.filter(certificate_expires_on__lt=today)

    if request.GET.get('export') == 'csv':
        return export_csv(qs, 'medicines_register', [
            ('Certificate Number', 'certificate_number'),
            ('Medicine Name', 'medicine_name'),
            ('Service', 'get_application_type_display'),
            ('Status', 'display_status'),
            ('Holder', 'holder_name'),
            ('Responsible Person', 'responsible_person'),
            ('Phone', lambda a: a.applicant.contact_phone),
            ('Email', lambda a: a.applicant.email),
            ('Region', lambda a: a.applicant.applicant_region),
            ('Issued On', 'certificate_issued_on'),
            ('Expires On', 'certificate_expires_on'),
            ('Renewals', 'renewal_count'),
            ('Legacy Entry', 'is_legacy'),
            ('Application Reference', 'reference_number'),
        ])

    page, query_string = paginate(request, qs)
    context = {
        'medicines': page,
        'query_string': query_string,
        'full_count': valid_count,
        'provisional_count': expired_count,
        'app_type': app_type,
        'status_filter': validity,
        'source': source,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/medicines.html', context)
