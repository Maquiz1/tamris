from .models import CustomUser
from medicines.models import MedicineApplication

def pending_reviews_count(request):
    """
    Injects the count of pending registration applications into the template context
    for staff members.
    """
    if request.user.is_authenticated:
        role_name = request.user.role.name if getattr(request.user, 'role', None) else None
        if role_name in ['Evaluator', 'Inspector', 'Accountant', 'Admin'] or request.user.is_superuser:
            count = CustomUser.objects.filter(
                is_onboarding_complete=True,
                registration_status='PENDING',
                role__name__in=['Individual Applicant', 'Company Applicant']
            ).count()
            
            prelim_count = MedicineApplication.objects.filter(status='UNDER_REVIEW').count()
            if getattr(request.user, 'is_finance', False) or getattr(request.user, 'is_admin', False):
                from medicines.models import Payment
                payment_count = Payment.objects.filter(is_verified=False).count()
            else:
                payment_count = 0
            sci_count = MedicineApplication.objects.filter(
                status__in=['PRELIMINARY_APPROVED', 'INSPECTION_COMPLETED']
            ).count()
            final_count = MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').count()
            
            insp_sched_count = MedicineApplication.objects.filter(
                application_type='CATEGORY_II',
                inspections__isnull=True,
                status__in=['SUBMITTED', 'UNDER_REVIEW', 'PRELIMINARY_APPROVED']
            ).distinct().count()
            
            return {
                'pending_reviews_count': count,
                'pending_preliminary_count': prelim_count,
                'pending_payment_count': payment_count,
                'pending_scientific_count': sci_count,
                'pending_final_count': final_count,
                'pending_inspection_scheduling_count': insp_sched_count,
                'total_pending_tasks': prelim_count + payment_count + sci_count + final_count + insp_sched_count,
                'total_user_tasks': count
            }
        else:
            # Applications (ALL apps of the user)
            all_applications = list(MedicineApplication.objects.filter(applicant=request.user).prefetch_related('payments'))
            
            my_applications_all_count = len(all_applications)
            my_applications_listed_count = sum(1 for app in all_applications if app.application_type == 'LISTING')
            my_applications_cat_ii_count = sum(1 for app in all_applications if app.application_type == 'CATEGORY_II')
            
            from medicines.models import Payment
            my_applications_payment_count = Payment.objects.filter(application__applicant=request.user).count()

            # Tasks
            tasks = [app for app in all_applications if app.requires_applicant_action]
            my_tasks_all_count = len(tasks)
            
            def is_payment_task(app):
                if 'PENDING' in app.status and 'FEE' in app.status:
                    payments = list(app.payments.all())
                    if payments:
                        payment = payments[-1]
                        if not payment.receipt_number and not payment.is_verified:
                            return True
                return False

            payment_tasks = [app for app in tasks if is_payment_task(app)]
            my_tasks_payment_count = len(payment_tasks)
            
            my_tasks_listed_count = sum(1 for app in tasks if not is_payment_task(app) and app.application_type == 'LISTING')
            my_tasks_cat_ii_count = sum(1 for app in tasks if not is_payment_task(app) and app.application_type == 'CATEGORY_II')
            
            return {
                'pending_reviews_count': 0,
                'pending_preliminary_count': 0,
                'pending_payment_count': 0,
                'pending_scientific_count': 0,
                'total_pending_tasks': 0,
                'total_user_tasks': 0,
                'my_applications_all_count': my_applications_all_count,
                'my_applications_listed_count': my_applications_listed_count,
                'my_applications_cat_ii_count': my_applications_cat_ii_count,
                'my_applications_payment_count': my_applications_payment_count,
                'my_tasks_all_count': my_tasks_all_count,
                'my_tasks_listed_count': my_tasks_listed_count,
                'my_tasks_cat_ii_count': my_tasks_cat_ii_count,
                'my_tasks_payment_count': my_tasks_payment_count,
            }
            
    return {
        'pending_reviews_count': 0,
        'pending_preliminary_count': 0,
        'pending_payment_count': 0,
        'pending_scientific_count': 0,
        'total_pending_tasks': 0,
        'total_user_tasks': 0,
        'applicant_listed_count': 0,
        'applicant_registered_count': 0,
        'applicant_tasks_count': 0
    }
