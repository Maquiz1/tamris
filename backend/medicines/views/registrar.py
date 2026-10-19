from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from medicines import services, legacy
from medicines.models import MedicineApplication
from users.models import LegacyClaim


def _registrar_only(user):
    return user.is_registrar or user.is_admin


@login_required
def registrar_dashboard_view(request):
    if not _registrar_only(request.user):
        return redirect('users:dashboard')
    context = {
        'final_count': MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').count(),
        'legacy_count': legacy.legacy_pending_queryset().count(),
        'claim_count': LegacyClaim.objects.filter(status='PENDING').count(),
        'issued_this_year': MedicineApplication.objects.filter(certificate_issued_on__year=timezone.localdate().year, is_legacy=False).count(),
    }
    return render(request, 'medicines/registrar/dashboard.html', context)


@login_required
def final_approval_list_view(request):
    if not _registrar_only(request.user):
        return redirect('users:dashboard')
    show = request.GET.get('show', 'pending')
    if show == 'decided':
        qs = MedicineApplication.objects.filter(final_approved_at__isnull=False, is_legacy=False).order_by('-final_approved_at')
    else:
        qs = MedicineApplication.objects.filter(status='PENDING_FINAL_APPROVAL').order_by('updated_at')
    applications = Paginator(qs, 15).get_page(request.GET.get('page'))
    return render(request, 'medicines/registrar/final_list.html', {'applications': applications, 'show': show})


@login_required
def final_approval_detail_view(request, pk):
    if not _registrar_only(request.user):
        return redirect('users:dashboard')
    application = get_object_or_404(MedicineApplication, pk=pk)
    if request.method == 'POST':
        if not request.user.is_registrar:
            messages.error(request, 'Only a user with the Registrar role can approve certificates.')
            return redirect('medicines:final_approval_detail', pk=pk)
        action = request.POST.get('action')
        reason = (request.POST.get('reason') or '').strip()
        try:
            if action == 'approve':
                application = services.issue_certificate(application, request.user)
                messages.success(request, f'Certificate {application.certificate_number} issued for {application.medicine_name}.')
            elif action == 'refuse':
                services.refuse_final_approval(application, request.user, reason)
                messages.warning(request, f'Final approval refused for {application.medicine_name}.')
        except services.WorkflowError as e:
            messages.error(request, str(e))
            return redirect('medicines:final_approval_detail', pk=pk)
        return redirect('medicines:final_approval_list')
    return render(request, 'medicines/registrar/final_detail.html', {
        'application': application,
        'payments': application.payments.order_by('created_at'),
        'inspections': application.inspections.order_by('-created_at'),
        'evaluation': getattr(application, 'evaluation', None),
    })


@login_required
def legacy_verification_list_view(request):
    if not _registrar_only(request.user):
        return redirect('users:dashboard')
    records = Paginator(legacy.legacy_pending_queryset().order_by('created_at'), 15).get_page(request.GET.get('page'))
    return render(request, 'medicines/registrar/legacy_list.html', {'records': records})


@login_required
def legacy_verification_detail_view(request, pk):
    if not (_registrar_only(request.user) or request.user.is_data_clerk):
        return redirect('users:dashboard')
    application = get_object_or_404(MedicineApplication.all_objects, pk=pk, is_legacy=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        reason = (request.POST.get('reason') or '').strip()
        try:
            if action in ('verify', 'return') and not request.user.is_registrar:
                raise services.WorkflowError('Only a user with the Registrar role can verify legacy certificates.')
            if action == 'verify':
                legacy.verify_legacy_certificate(application, request.user)
                messages.success(request, f'Certificate {application.certificate_number} verified. It is now active.')
            elif action == 'return':
                legacy.return_legacy_record(application, request.user, reason)
                messages.warning(request, 'Record returned to the Data Clerk for correction.')
            elif action == 'void':
                if not _registrar_only(request.user):
                    raise services.WorkflowError('Only a Registrar or administrator can void a record.')
                legacy.void_legacy_record(application, request.user, reason)
                messages.warning(request, 'Record voided. Its history is kept.')
        except services.WorkflowError as e:
            messages.error(request, str(e))
            return redirect('medicines:legacy_verification_detail', pk=pk)
        return redirect('medicines:legacy_verification_list' if _registrar_only(request.user) else 'medicines:legacy_dashboard')
    return render(request, 'medicines/registrar/legacy_detail.html', {
        'application': application,
        'payments': application.payments.order_by('created_at'),
    })


@login_required
def claim_list_view(request):
    if not _registrar_only(request.user):
        return redirect('users:dashboard')
    if request.method == 'POST':
        claim = get_object_or_404(LegacyClaim, pk=request.POST.get('claim_id'))
        note = (request.POST.get('note') or '').strip()
        try:
            if request.POST.get('action') == 'confirm':
                legacy.confirm_claim(claim, request.user, note)
                messages.success(request, f'Records linked to {claim.new_user.email}.')
            else:
                legacy.reject_claim(claim, request.user, note)
                messages.warning(request, 'Request rejected.')
        except services.WorkflowError as e:
            messages.error(request, str(e))
        return redirect('medicines:claim_list')
    claims = LegacyClaim.objects.select_related('new_user', 'legacy_user').order_by('status', '-created_at')
    return render(request, 'medicines/registrar/claims.html', {'claims': claims})
