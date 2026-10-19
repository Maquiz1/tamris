from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from medicines.forms import PreliminaryEvaluationForm, ScientificEvaluationForm
from medicines.models import MedicineApplication, MedicineEvaluation, FeeInactiveError
from medicines import services
from users.emails import notify_applicant_application_status
from medicines.views.utils import get_filtered_applications


def scientific_ready_status(application):
    """Listing goes straight to scientific evaluation; Category II only after inspection."""
    return 'PRELIMINARY_APPROVED' if application.application_type == 'LISTING' else 'INSPECTION_COMPLETED'


@login_required
def staff_preliminary_list_view(request):
    if not (request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    list_filter = request.GET.get('filter', 'pending')
    if list_filter == 'pending':
        base_qs = MedicineApplication.objects.filter(status='UNDER_REVIEW', is_legacy=False).order_by('-submitted_at')
    else:
        base_qs = MedicineApplication.objects.filter(is_legacy=False).exclude(status__in=['DRAFT', 'PENDING_APPLICATION_FEE', 'PENDING_EVALUATION_FEE']).order_by('-submitted_at')
    (applications_list, query, status_filter, start_date, end_date) = get_filtered_applications(request, base_qs)
    paginator = Paginator(applications_list, 10)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)
    return render(request, 'medicines/staff/preliminary_list.html', {'applications': applications, 'total_applications': applications_list.count(), 'query': query, 'status_filter': status_filter, 'start_date': start_date, 'end_date': end_date, 'list_filter': list_filter})


@login_required
def staff_preliminary_detail_view(request, pk):
    if not (request.user.is_evaluator or request.user.is_admin):
        return redirect('users:dashboard')
    application = get_object_or_404(MedicineApplication, pk=pk)
    (evaluation, created) = MedicineEvaluation.objects.get_or_create(application=application)
    can_act = application.status == 'UNDER_REVIEW'
    if request.method == 'POST':
        if not can_act:
            messages.error(request, f'This application is at "{application.get_status_display()}", so preliminary screening decisions can no longer be made.')
            return redirect('medicines:staff_preliminary_detail', pk=pk)
        action = request.POST.get('action')
        evaluation_form = PreliminaryEvaluationForm(request.POST, instance=evaluation)
        if evaluation_form.is_valid():
            if action == 'conditions' and not (evaluation_form.cleaned_data.get('overall_comments') and evaluation_form.cleaned_data.get('sections_to_revise')):
                messages.error(request, 'To apply conditions, tick the sections the applicant may edit and write the conditions in the comments.')
                return render(request, 'medicines/staff/preliminary_detail.html', {'application': application, 'evaluation_form': evaluation_form, 'can_act': can_act})
            eval_instance = evaluation_form.save(commit=False)
            eval_instance.evaluator = request.user
            eval_instance.save()
            if action == 'approve':
                if application.application_type == 'CATEGORY_II':
                    try:
                        services.create_fee(application, 'inspection')
                    except FeeInactiveError:
                        messages.error(request, 'Cannot approve because the Inspection Fee is currently suspended.')
                        return redirect('medicines:staff_preliminary_list')
                    application.status = 'PENDING_INSPECTION_FEE'
                    application.save()
                    messages.success(request, f'Application for {application.medicine_name} passed preliminary screening. An Inspection Fee has been generated.')
                    notify_applicant_application_status(application, 'TAMRIS - Preliminary Screening Passed', 'Your application has passed the preliminary screening. Please pay the Inspection Fee and submit the control number so the site inspection can be scheduled.')
                else:
                    application.status = 'PRELIMINARY_APPROVED'
                    application.save()
                    messages.success(request, f'Application for {application.medicine_name} passed preliminary screening.')
                    notify_applicant_application_status(application, 'TAMRIS - Preliminary Screening Passed', 'Your application has passed the preliminary screening. It is now queued for Scientific Evaluation.')
            elif action == 'conditions':
                services.apply_conditions(application, 'preliminary', eval_instance.overall_comments)
                messages.warning(request, f'Conditions for improvement sent to the applicant for {application.medicine_name}.')
            elif action == 'reject':
                application.status = 'REJECTED'
                application.rejection_reason = eval_instance.overall_comments or 'Failed preliminary screening.'
                application.save()
                messages.error(request, f'Application for {application.medicine_name} rejected at preliminary screening.')
                notify_applicant_application_status(application, 'TAMRIS - Application Rejected', f'Your application has been rejected at the preliminary screening stage.\nReason: {application.rejection_reason}')
            return redirect('medicines:staff_preliminary_list')
    else:
        evaluation_form = PreliminaryEvaluationForm(instance=evaluation)
    return render(request, 'medicines/staff/preliminary_detail.html', {'application': application, 'evaluation_form': evaluation_form, 'can_act': can_act})


@login_required
def staff_scientific_list_view(request):
    if not (request.user.is_evaluator or request.user.is_admin or request.user.is_inspector or request.user.is_registrar):
        return redirect('users:dashboard')
    pending_q = MedicineApplication.objects.filter(is_legacy=False, status__in=['PRELIMINARY_APPROVED', 'INSPECTION_COMPLETED']).exclude(application_type='CATEGORY_II', status='PRELIMINARY_APPROVED')
    list_filter = request.GET.get('filter', 'pending')
    if list_filter == 'pending':
        base_qs = pending_q.order_by('-submitted_at')
    elif list_filter == 'payment':
        base_qs = MedicineApplication.objects.filter(status__in=['PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE']).order_by('-submitted_at')
    elif list_filter == 'final':
        base_qs = MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').order_by('-submitted_at')
    elif list_filter == 'approved':
        base_qs = MedicineApplication.objects.filter(status__in=['PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION'], is_legacy=False).order_by('-submitted_at')
    else:
        base_qs = MedicineApplication.objects.filter(is_legacy=False, status__in=['PRELIMINARY_APPROVED', 'INSPECTION_COMPLETED', 'PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE', 'PENDING_FINAL_APPROVAL', 'PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION', 'CONDITIONS_APPLIED', 'REJECTED']).order_by('-submitted_at')
    (applications_list, query, status_filter, start_date, end_date) = get_filtered_applications(request, base_qs)
    paginator = Paginator(applications_list, 10)
    page_number = request.GET.get('page')
    applications = paginator.get_page(page_number)
    return render(request, 'medicines/staff/scientific_list.html', {
        'applications': applications, 'total_applications': applications_list.count(),
        'query': query, 'status_filter': status_filter, 'start_date': start_date, 'end_date': end_date,
        'list_filter': list_filter,
        'pending_count': pending_q.count(),
        'payment_count': MedicineApplication.objects.filter(status__in=['PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE']).count(),
        'final_count': MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').count(),
        'approved_count': MedicineApplication.objects.filter(status__in=['PROVISIONAL_REGISTRATION', 'FULL_REGISTRATION'], is_legacy=False).count(),
    })


@login_required
def staff_scientific_detail_view(request, pk):
    # Inspectors and Registrars may read this page; only evaluators (or admins) decide.
    if not (request.user.is_evaluator or request.user.is_admin or request.user.is_inspector or request.user.is_registrar):
        return redirect('users:dashboard')
    application = get_object_or_404(MedicineApplication, pk=pk)
    (evaluation, created) = MedicineEvaluation.objects.get_or_create(application=application)
    can_decide = request.user.is_evaluator or request.user.is_admin
    can_act = can_decide and application.status == scientific_ready_status(application)
    if request.method == 'POST':
        if not can_decide:
            messages.error(request, 'Only users with evaluation access can make evaluation decisions.')
            return redirect('medicines:staff_scientific_list')
        if not can_act:
            messages.error(request, f'This application is at "{application.get_status_display()}", so scientific evaluation decisions cannot be made now.')
            return redirect('medicines:staff_scientific_detail', pk=pk)

        action = request.POST.get('action')
        evaluation_form = ScientificEvaluationForm(request.POST, instance=evaluation)
        if evaluation_form.is_valid():
            if action in ('conditions', 'reject') and not evaluation_form.cleaned_data.get('overall_comments'):
                messages.error(request, 'Write your comments for the applicant before applying conditions or rejecting.')
                return render(request, 'medicines/staff/scientific_detail.html', {'application': application, 'evaluation_form': evaluation_form, 'can_act': can_act})
            if action == 'conditions' and not evaluation_form.cleaned_data.get('sections_to_revise') and not request.POST.get('requires_reinspection'):
                messages.error(request, 'Tick the sections the applicant may edit, or ask for a re-inspection.')
                return render(request, 'medicines/staff/scientific_detail.html', {'application': application, 'evaluation_form': evaluation_form, 'can_act': can_act})
            eval_instance = evaluation_form.save(commit=False)
            eval_instance.evaluator = request.user
            eval_instance.save()
            if action == 'provisional':
                try:
                    payment = services.give_provisional(application)
                except FeeInactiveError:
                    messages.error(request, 'Cannot give provisional approval because the final fee is currently suspended.')
                    return redirect('medicines:staff_scientific_list')
                messages.success(request, f'Provisional approval given. {payment.get_payment_type_display()} generated for {application.medicine_name}.')
            elif action == 'conditions':
                services.apply_conditions(application, 'scientific', eval_instance.overall_comments, requires_reinspection=bool(request.POST.get('requires_reinspection')))
                messages.warning(request, f'Conditions for improvement sent to the applicant for {application.medicine_name}.')
            elif action == 'reject':
                application.status = 'REJECTED'
                application.rejection_reason = eval_instance.overall_comments
                application.save()
                messages.error(request, f'Application for {application.medicine_name} has been rejected.')
                notify_applicant_application_status(application, 'TAMRIS - Application Rejected', f'Unfortunately, your application for {application.medicine_name} has been rejected after Scientific Evaluation.\nReason and recommendations: {eval_instance.overall_comments}')
            return redirect('medicines:staff_scientific_list')
    else:
        evaluation_form = ScientificEvaluationForm(instance=evaluation)
    return render(request, 'medicines/staff/scientific_detail.html', {'application': application, 'evaluation_form': evaluation_form, 'can_act': can_act})
