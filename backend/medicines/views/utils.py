from django.db.models import Q


def get_filtered_applications(request, base_queryset):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if query:
        if query in ['LISTING', 'CATEGORY_II']:
            base_queryset = base_queryset.filter(application_type=query)
        else:
            base_queryset = base_queryset.filter(
                Q(medicine_name__icontains=query)
                | Q(reference_number__icontains=query)
                | Q(certificate_number__icontains=query)
                | Q(applicant__email__icontains=query)
                | Q(applicant__applicant_profile__individual__first_name__icontains=query)
                | Q(applicant__applicant_profile__individual__last_name__icontains=query)
                | Q(applicant__applicant_profile__organization__organization_name__icontains=query)
            ).distinct()
    if status_filter:
        base_queryset = base_queryset.filter(status=status_filter)
    if start_date:
        base_queryset = base_queryset.filter(submitted_at__date__gte=start_date)
    if end_date:
        base_queryset = base_queryset.filter(submitted_at__date__lte=end_date)
    return (base_queryset, query, status_filter, start_date, end_date)
