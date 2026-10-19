from .models import CustomUser, LegacyClaim
from medicines.models import MedicineApplication

EMPTY = {
    'pending_reviews_count': 0,
    'pending_preliminary_count': 0,
    'pending_payment_count': 0,
    'pending_scientific_count': 0,
    'pending_final_count': 0,
    'pending_inspection_scheduling_count': 0,
    'pending_legacy_count': 0,
    'pending_claim_count': 0,
    'returned_legacy_count': 0,
    'total_pending_tasks': 0,
    'total_user_tasks': 0,
    'applicant_listed_count': 0,
    'applicant_registered_count': 0,
    'applicant_tasks_count': 0,
}


def pending_reviews_count(request):
    """
    Injects the counts shown as badges in the sidebar and dashboards.
    """
    if not request.user.is_authenticated:
        return EMPTY

    user = request.user
    if user.is_staff_member:
        from medicines.models import Payment
        from medicines.legacy import legacy_pending_queryset
        from medicines.views.inspections import awaiting_scheduling

        count = CustomUser.objects.filter(
            is_onboarding_complete=True,
            registration_status='PENDING',
            role__name__in=['Individual Applicant', 'Company Applicant']
        ).count()
        prelim_count = MedicineApplication.objects.filter(status='UNDER_REVIEW', is_legacy=False).count()
        payment_count = Payment.objects.filter(is_verified=False, control_number__isnull=False).exclude(control_number='').count() if (user.is_finance or user.is_admin) else 0
        sci_count = (
            MedicineApplication.objects.filter(status__in=['PRELIMINARY_APPROVED', 'INSPECTION_COMPLETED'], is_legacy=False)
            .exclude(application_type='CATEGORY_II', status='PRELIMINARY_APPROVED').count()
        )
        final_count = MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').count()
        insp_sched_count = awaiting_scheduling().count()
        legacy_count = legacy_pending_queryset().count()
        claim_count = LegacyClaim.objects.filter(status='PENDING').count()
        returned_count = MedicineApplication.objects.filter(is_legacy=True, is_void=False, legacy_verification_status='RETURNED').count()

        return {
            **EMPTY,
            'pending_reviews_count': count,
            'pending_preliminary_count': prelim_count,
            'pending_payment_count': payment_count,
            'pending_scientific_count': sci_count,
            'pending_final_count': final_count,
            'pending_inspection_scheduling_count': insp_sched_count,
            'pending_legacy_count': legacy_count,
            'pending_claim_count': claim_count,
            'returned_legacy_count': returned_count,
            'total_pending_tasks': prelim_count + payment_count + sci_count + final_count + insp_sched_count,
            'total_user_tasks': count,
        }

    from medicines.views.applicant import visible_applications
    all_applications = list(visible_applications(user).prefetch_related('payments'))

    my_applications_all_count = len(all_applications)
    my_applications_listed_count = sum(1 for app in all_applications if app.application_type == 'LISTING')
    my_applications_cat_ii_count = sum(1 for app in all_applications if app.application_type == 'CATEGORY_II')

    from medicines.models import Payment
    my_applications_payment_count = Payment.objects.filter(application__in=[a.pk for a in all_applications]).count()

    tasks = [app for app in all_applications if app.requires_applicant_action]

    def is_payment_task(app):
        if 'PENDING' in app.status and 'FEE' in app.status:
            payments = list(app.payments.all())
            if payments:
                payment = payments[-1]
                if not payment.control_number and not payment.is_verified:
                    return True
        return app.status == 'FULL_REGISTRATION'  # only renewal payments make a certified medicine a task

    payment_tasks = [app for app in tasks if is_payment_task(app)]

    return {
        **EMPTY,
        'my_applications_all_count': my_applications_all_count,
        'my_applications_listed_count': my_applications_listed_count,
        'my_applications_cat_ii_count': my_applications_cat_ii_count,
        'my_applications_payment_count': my_applications_payment_count,
        'my_tasks_all_count': len(tasks),
        'my_tasks_listed_count': sum(1 for app in tasks if not is_payment_task(app) and app.application_type == 'LISTING'),
        'my_tasks_cat_ii_count': sum(1 for app in tasks if not is_payment_task(app) and app.application_type == 'CATEGORY_II'),
        'my_tasks_payment_count': len(payment_tasks),
    }
