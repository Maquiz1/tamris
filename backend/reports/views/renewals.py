import datetime

from django.shortcuts import render
from django.utils import timezone

from medicines.models import MedicineApplication, Payment
from reports.views.utils import report_access, paginate, export_csv, visible_applications

WINDOWS = [
    ('expired', 'Expired'),
    ('7', 'Within 7 days'),
    ('30', 'Within 30 days'),
    ('90', 'Within 90 days'),
]


def renewal_state(app):
    payment = next((p for p in app.payments.all() if p.payment_type in Payment.RENEWAL_TYPES and not p.is_verified), None)
    if payment is None:
        return 'Not started'
    return 'Paid, waiting for Finance' if payment.control_number else 'Started, not paid'


@report_access('renewals')
def renewals_report_view(request):
    """Certificates that have expired or expire within 90 days, with who to contact."""
    today = timezone.localdate()
    base = (
        visible_applications(MedicineApplication.objects.filter(status='FULL_REGISTRATION'))
        .exclude(certificate_expires_on__isnull=True)
        .select_related('applicant')
        .prefetch_related('payments')
    )
    counts = {
        'expired': base.filter(certificate_expires_on__lt=today).count(),
        '7': base.filter(certificate_expires_on__gte=today, certificate_expires_on__lte=today + datetime.timedelta(days=7)).count(),
        '30': base.filter(certificate_expires_on__gte=today, certificate_expires_on__lte=today + datetime.timedelta(days=30)).count(),
        '90': base.filter(certificate_expires_on__gte=today, certificate_expires_on__lte=today + datetime.timedelta(days=90)).count(),
    }

    window = request.GET.get('window', '90')
    type_filter = request.GET.get('type', '')
    if window == 'expired':
        qs = base.filter(certificate_expires_on__lt=today).order_by('-certificate_expires_on')
    else:
        days = int(window) if window in ('7', '30', '90') else 90
        window = str(days)
        qs = base.filter(certificate_expires_on__gte=today, certificate_expires_on__lte=today + datetime.timedelta(days=days)).order_by('certificate_expires_on')
    if type_filter:
        qs = qs.filter(application_type=type_filter)

    if request.GET.get('export') == 'csv':
        return export_csv(qs, f'renewals_{window}', [
            ('Certificate Number', 'certificate_number'),
            ('Medicine Name', 'medicine_name'),
            ('Service', 'get_application_type_display'),
            ('Holder', 'holder_name'),
            ('Responsible Person', 'responsible_person'),
            ('Phone', lambda a: a.applicant.contact_phone),
            ('Email', lambda a: a.applicant.email),
            ('Region', lambda a: a.applicant.applicant_region),
            ('Expires On', 'certificate_expires_on'),
            ('Days Left', 'days_to_expiry'),
            ('Renewal', renewal_state),
            ('Reminders Sent', lambda a: ', '.join(str(r) for r in (a.renewal_reminders_sent or []))),
        ])

    page, query_string = paginate(request, qs)
    for app in page:
        app.renewal_state = renewal_state(app)
    return render(request, 'reports/renewals.html', {
        'certificates': page,
        'query_string': query_string,
        'counts': counts,
        'window': window,
        'windows': WINDOWS,
        'type_filter': type_filter,
        'today': today,
    })
