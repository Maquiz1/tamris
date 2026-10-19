import datetime

from django.db import models
from django.db.models import Case, Count, Q, Sum, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.shortcuts import render
from django.utils import timezone

from core.utils.fees import FEE_TYPES
from medicines.models import Payment
from reports.views.utils import report_access, date_range, filter_dates, paginate, as_json, export_csv

MONEY = models.DecimalField(max_digits=14, decimal_places=2)
ZERO = Value(0, output_field=MONEY)

# What was actually received: the amount paid if recorded, otherwise the bill.
# Paper-era payments count only when the Data Clerk entered a verified amount.
RECEIVED = Case(
    When(paid_before_system=True, then=Coalesce('amount_paid', ZERO)),
    default=Coalesce('amount_paid', 'amount'),
    output_field=MONEY,
)
FEE_LABELS = dict(FEE_TYPES)


def short_fee_label(code):
    label = FEE_LABELS.get(code, code)
    return label.split(': ', 1)[-1]


def submitted_q():
    return Q(is_verified=False) & Q(control_number__isnull=False) & ~Q(control_number='')


def awaiting_q():
    return Q(is_verified=False) & (Q(control_number__isnull=True) | Q(control_number=''))


@report_access('payments')
def payments_report_view(request):
    qs = Payment.objects.select_related('application', 'application__applicant', 'verified_by').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    source = request.GET.get('source', '')
    fee_filter = request.GET.get('fee', '')
    start_date, end_date, start_dt, end_dt = date_range(request)

    if status_filter == 'VERIFIED':
        qs = qs.filter(is_verified=True)
    elif status_filter == 'SUBMITTED':
        qs = qs.filter(submitted_q())
    elif status_filter == 'PENDING':
        qs = qs.filter(awaiting_q())
    if source == 'system':
        qs = qs.filter(paid_before_system=False)
    elif source == 'legacy':
        qs = qs.filter(paid_before_system=True)
    if fee_filter:
        qs = qs.filter(payment_type=fee_filter)
    qs = filter_dates(qs, 'created_at', start_dt, end_dt)

    if request.GET.get('export') == 'csv':
        return export_csv(qs, 'payments_report', [
            ('Payment ID', 'id'),
            ('Application Reference', lambda p: p.application.reference_number),
            ('Medicine', lambda p: p.application.medicine_name),
            ('Applicant', lambda p: p.application.holder_name),
            ('Applicant Email', lambda p: p.application.applicant.email),
            ('Fee Type', 'get_payment_type_display'),
            ('Amount Billed (TZS)', 'amount'),
            ('Amount Paid (TZS)', 'amount_paid'),
            ('Control Number', 'control_number'),
            ('Receipt Number', 'receipt_number'),
            ('Verified', 'is_verified'),
            ('Verified By', lambda p: p.verified_by.display_name if p.verified_by else ''),
            ('Verified At', 'verified_at'),
            ('Paid Before the System', 'paid_before_system'),
            ('Created', 'created_at'),
        ])

    fee_summary = list(
        qs.values('payment_type').annotate(
            payment_count=Count('id'),
            awaiting_amount=Coalesce(Sum('amount', filter=Q(is_verified=False)), ZERO),
            verified_amount=Coalesce(Sum(RECEIVED, filter=Q(is_verified=True, paid_before_system=False)), ZERO),
            legacy_amount=Coalesce(Sum(RECEIVED, filter=Q(is_verified=True, paid_before_system=True)), ZERO),
        ).order_by('payment_type')
    )
    for item in fee_summary:
        item['label'] = short_fee_label(item['payment_type'])
        item['service'] = 'Listing' if item['payment_type'].startswith('LISTING') else 'Category II'
        item['total_amount'] = item['verified_amount'] + item['legacy_amount']

    page, query_string = paginate(request, qs)
    context = {
        'payments': page,
        'query_string': query_string,
        'fee_summary': fee_summary,
        'total_payment_count': sum(i['payment_count'] for i in fee_summary),
        'total_pending_amount': sum(i['awaiting_amount'] for i in fee_summary),
        'total_verified_amount': sum(i['verified_amount'] for i in fee_summary),
        'total_legacy_amount': sum(i['legacy_amount'] for i in fee_summary),
        'total_all_amount': sum(i['total_amount'] for i in fee_summary),
        'fee_chart_labels': as_json([f"{i['service']}: {i['label']}" for i in fee_summary]),
        'fee_chart_data': as_json([float(i['verified_amount']) for i in fee_summary]),
        'verified_count': qs.filter(is_verified=True).count(),
        'pending_count': qs.filter(submitted_q()).count(),
        'awaiting_count': qs.filter(awaiting_q()).count(),
        'status_filter': status_filter,
        'source': source,
        'fee_filter': fee_filter,
        'fee_choices': [(code, f"{'Listing' if code.startswith('LISTING') else 'Category II'}: {short_fee_label(code)}") for code, _ in FEE_TYPES],
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'reports/payments.html', context)


def month_starts(first, last):
    months = []
    current = first.replace(day=1)
    while current <= last:
        months.append(current)
        current = (current + datetime.timedelta(days=32)).replace(day=1)
    return months


@report_access('revenue')
def revenue_report_view(request):
    """Money received per month and per fee, by the date Finance verified it."""
    start_date, end_date, start_dt, end_dt = date_range(request)
    today = timezone.localdate()
    if not end_date:
        end_date = today
        end_dt = datetime.datetime.combine(end_date, datetime.time.max, tzinfo=timezone.get_current_timezone())
    if not start_date:
        start_date = (end_date.replace(day=1) - datetime.timedelta(days=330)).replace(day=1)  # last 12 months
        start_dt = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=timezone.get_current_timezone())

    verified = filter_dates(Payment.objects.filter(is_verified=True, paid_before_system=False), 'verified_at', start_dt, end_dt)
    rows = (
        verified.annotate(month=TruncMonth('verified_at', tzinfo=timezone.get_current_timezone()))
        .values('month', 'payment_type')
        .annotate(received=Sum(RECEIVED), count=Count('id'))
        .order_by('month')
    )

    months = month_starts(start_date, end_date)
    month_keys = [m.strftime('%Y-%m') for m in months]
    fee_codes = [code for code, _ in FEE_TYPES]
    grid = {code: {key: 0 for key in month_keys} for code in fee_codes}
    month_totals = {key: 0 for key in month_keys}
    for row in rows:
        key = row['month'].strftime('%Y-%m')
        if key not in month_totals:
            continue
        grid.setdefault(row['payment_type'], {k: 0 for k in month_keys})[key] += row['received']
        month_totals[key] += row['received']

    table = []
    for code in fee_codes:
        values = [grid[code][key] for key in month_keys]
        if any(values):
            table.append({
                'label': short_fee_label(code),
                'service': 'Listing' if code.startswith('LISTING') else 'Category II',
                'values': values,
                'total': sum(values),
            })
    month_labels = [m.strftime('%b %Y') for m in months]

    if request.GET.get('export') == 'csv':
        lines = [dict(name=f"{r['service']}: {r['label']}", values=r['values'], total=r['total']) for r in table]
        lines.append(dict(name='Total', values=[month_totals[k] for k in month_keys], total=sum(month_totals.values())))
        columns = [('Fee', lambda r: r['name'])]
        columns += [(label, (lambda i: lambda r: r['values'][i])(i)) for i, label in enumerate(month_labels)]
        columns.append(('Total', lambda r: r['total']))
        return export_csv(lines, 'revenue_by_month', columns)

    listing_total = sum(r['total'] for r in table if r['service'] == 'Listing')
    category_ii_total = sum(r['total'] for r in table if r['service'] == 'Category II')
    legacy_total = Payment.objects.filter(is_verified=True, paid_before_system=True).aggregate(v=Coalesce(Sum(RECEIVED), ZERO))['v']

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'month_labels': month_labels,
        'month_totals': [month_totals[k] for k in month_keys],
        'table': table,
        'grand_total': sum(month_totals.values()),
        'listing_total': listing_total,
        'category_ii_total': category_ii_total,
        'legacy_total': legacy_total,
        'payment_count': verified.count(),
        'chart_labels': as_json(month_labels),
        'chart_listing': as_json([float(sum(grid[c][k] for c in fee_codes if c.startswith('LISTING'))) for k in month_keys]),
        'chart_category_ii': as_json([float(sum(grid[c][k] for c in fee_codes if c.startswith('CAT_II'))) for k in month_keys]),
    }
    return render(request, 'reports/revenue.html', context)
