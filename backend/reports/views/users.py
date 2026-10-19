from django.shortcuts import render

from users.models import CustomUser
from reports.views.utils import report_access, paginate, export_csv


@report_access('users')
def users_report_view(request):
    # Superusers are managed in Django admin only
    qs = CustomUser.objects.exclude(is_superuser=True).select_related('role').prefetch_related('additional_roles').order_by('-date_joined')
    if request.GET.get('export') == 'csv':
        return export_csv(qs, 'users_report', [
            ('ID', 'id'),
            ('Name', 'display_name'),
            ('Email', 'email'),
            ('Phone', 'contact_phone'),
            ('Roles', lambda u: ', '.join(u.all_roles)),
            ('Region', 'applicant_region'),
            ('Registration Status', 'registration_status'),
            ('Active', 'is_active'),
            ('Legacy Entry', 'is_legacy'),
            ('Date Joined', 'date_joined'),
        ])
    page, query_string = paginate(request, qs)
    return render(request, 'reports/users.html', {'users': page, 'query_string': query_string})
