import csv
import datetime
import json
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone


def is_staff_check(user):
    return user.is_active and (user.is_staff or getattr(user, 'is_staff_member', False))


# Who may open which report. Matches the Reports & Registry menu.
REPORT_ACCESS = {
    'dashboard': lambda u: u.is_staff_member,
    'applications': lambda u: u.is_admin or u.is_evaluator or u.is_registrar or u.is_committee or u.is_data_clerk,
    'evaluations': lambda u: u.is_admin or u.is_evaluator or u.is_registrar or u.is_committee,
    'medicines': lambda u: u.is_admin or u.is_evaluator or u.is_registrar or u.is_committee or u.is_data_clerk,
    'inspections': lambda u: u.is_admin or u.is_inspector or u.is_evaluator or u.is_registrar or u.is_committee,
    'payments': lambda u: u.is_admin or u.is_finance or u.is_registrar or u.is_committee,
    'revenue': lambda u: u.is_admin or u.is_finance or u.is_registrar or u.is_committee,
    'renewals': lambda u: u.is_admin or u.is_evaluator or u.is_registrar or u.is_committee or u.is_finance,
    'users': lambda u: u.is_admin or u.is_committee,
}


def report_access(name):
    """Allow a report only to the roles that see it in the menu; others go back to their dashboard."""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            user = request.user
            if not (user.is_active and (user.is_superuser or REPORT_ACCESS[name](user))):
                return redirect('users:dashboard')
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def date_range(request):
    """Start and end of the chosen dates as aware datetimes (end date included). Bad input is ignored."""
    def parse(value):
        try:
            return datetime.date.fromisoformat(value) if value else None
        except ValueError:
            return None
    start, end = parse(request.GET.get('start_date')), parse(request.GET.get('end_date'))
    tz = timezone.get_current_timezone()
    start_dt = datetime.datetime.combine(start, datetime.time.min, tzinfo=tz) if start else None
    end_dt = datetime.datetime.combine(end, datetime.time.max, tzinfo=tz) if end else None
    return start, end, start_dt, end_dt


def filter_dates(qs, field, start_dt, end_dt):
    if start_dt:
        qs = qs.filter(**{f'{field}__gte': start_dt})
    if end_dt:
        qs = qs.filter(**{f'{field}__lte': end_dt})
    return qs


def paginate(request, qs, per_page=25):
    """One page of results plus the query string for the other pages (filters kept)."""
    page = Paginator(qs, per_page).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return page, params.urlencode()


def as_json(value):
    """Chart data for templates, safe for labels with quotes."""
    return json.dumps(value, default=str)


def export_csv(rows, filename, columns):
    """
    Write rows to CSV. Each column is (label, getter); a getter is an attribute
    name (methods are called) or a function taking the row.
    Older calls passing [{'name': ..., 'label': ...}] still work.
    """
    if columns and isinstance(columns[0], dict):
        columns = [(c['label'], c['name']) for c in columns]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{timezone.now():%Y%m%d}.csv"'
    response.write('﻿')  # lets Excel read Swahili characters correctly
    writer = csv.writer(response)
    writer.writerow([label for label, _ in columns])
    for obj in rows:
        row = []
        for _, getter in columns:
            if callable(getter):
                value = getter(obj)
            else:
                value = getattr(obj, getter, '')
                if callable(value):
                    value = value()
            if isinstance(value, bool):
                value = 'Yes' if value else 'No'
            elif isinstance(value, datetime.datetime):
                value = timezone.localtime(value).strftime('%Y-%m-%d %H:%M')
            row.append('' if value is None else value)
        writer.writerow(row)
    return response


def visible_applications(qs):
    """Leave out voided records and paper records the Registrar has not verified yet."""
    return qs.filter(is_void=False).exclude(is_legacy=True, legacy_verification_status__in=['PENDING', 'RETURNED'])
