from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from medicines import legacy, services
from medicines.forms import LegacyApplicantForm, LegacyMedicineForm, LegacyPaymentFormSet, SystemSettingsForm, CounterForm
from medicines.models import MedicineApplication, NumberSequence, SystemSettings


def _clerk_only(user):
    return user.is_data_clerk or user.is_admin


@login_required
def legacy_dashboard_view(request):
    if not (_clerk_only(request.user) or request.user.is_registrar):
        return redirect('users:dashboard')
    qs = MedicineApplication.all_objects.filter(is_legacy=True).select_related('applicant').order_by('-created_at')
    show = request.GET.get('show', 'all')
    if show == 'returned':
        qs = qs.filter(legacy_verification_status='RETURNED', is_void=False)
    elif show == 'pending':
        qs = qs.filter(legacy_verification_status='PENDING', is_void=False)
    elif show == 'verified':
        qs = qs.filter(legacy_verification_status='VERIFIED', is_void=False)
    elif show == 'rejected':
        qs = qs.filter(status='REJECTED', is_void=False)
    elif show == 'void':
        qs = qs.filter(is_void=True)
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(Q(medicine_name__icontains=query) | Q(certificate_number__icontains=query) | Q(applicant__email__icontains=query))
    all_legacy = MedicineApplication.all_objects.filter(is_legacy=True, is_void=False)
    counts = {
        'total': all_legacy.count(),
        'pending': all_legacy.filter(legacy_verification_status='PENDING').count(),
        'returned': all_legacy.filter(legacy_verification_status='RETURNED').count(),
        'verified': all_legacy.filter(legacy_verification_status='VERIFIED').count(),
        'rejected': all_legacy.filter(status='REJECTED').count(),
    }
    records = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'medicines/legacy/dashboard.html', {'records': records, 'show': show, 'query': query, 'counts': counts})


@login_required
def legacy_applicant_create_view(request):
    if not _clerk_only(request.user):
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = LegacyApplicantForm(request.POST, request.FILES)
        if form.is_valid():
            user = legacy.create_legacy_applicant(form.cleaned_data, request.FILES, request.user)
            messages.success(request, f'Applicant {user.display_name} saved. You can now enter their medicines.')
            return redirect(f"{reverse('medicines:legacy_medicine_create')}?applicant={user.pk}")
    else:
        form = LegacyApplicantForm()
    return render(request, 'medicines/legacy/applicant_form.html', {'form': form})


@login_required
def legacy_medicine_create_view(request, pk=None):
    if not _clerk_only(request.user):
        return redirect('users:dashboard')
    instance = None
    if pk:
        instance = get_object_or_404(MedicineApplication, pk=pk, is_legacy=True, is_void=False)
        if instance.legacy_verification_status == 'VERIFIED':
            messages.error(request, 'This record has been verified and can no longer be edited.')
            return redirect('medicines:legacy_dashboard')
    if request.method == 'POST':
        form = LegacyMedicineForm(request.POST, request.FILES, instance=instance)
        payments = LegacyPaymentFormSet(request.POST, prefix='pay') if instance is None else None
        if form.is_valid() and (payments is None or payments.is_valid()):
            app = legacy.save_legacy_medicine(form, payments, request.user)
            if app.status == 'FULL_REGISTRATION':
                messages.success(request, f'{app.medicine_name} saved. Certificate {app.certificate_number} is waiting for Registrar verification.')
            else:
                messages.success(request, f'Rejected application {app.medicine_name} saved for history.')
            return redirect('medicines:legacy_dashboard')
    else:
        initial = {}
        if request.GET.get('applicant'):
            initial['applicant'] = request.GET['applicant']
        form = LegacyMedicineForm(instance=instance, initial=initial)
        payments = LegacyPaymentFormSet(prefix='pay') if instance is None else None
    return render(request, 'medicines/legacy/medicine_form.html', {'form': form, 'payments': payments, 'instance': instance})


@login_required
def legacy_claim_request_view(request, legacy_user_id):
    """An applicant asks to link records that a Data Clerk entered from paper."""
    if request.method != 'POST':
        return redirect('users:dashboard')
    match = next((u for u in legacy.find_legacy_matches(request.user) if u.pk == legacy_user_id), None)
    if match is None:
        messages.error(request, 'These records do not match your profile.')
        return redirect('users:dashboard')
    legacy.request_claim(request.user, match)
    messages.success(request, 'Your request has been sent. The Council will confirm it and the records will appear in your account.')
    return redirect('users:dashboard')


@login_required
def system_settings_view(request):
    if not request.user.is_admin:
        return redirect('users:dashboard')
    settings_obj = SystemSettings.load()
    year = timezone.localdate().year
    listing_seq, _ = NumberSequence.objects.get_or_create(kind=NumberSequence.CERT_LISTING, year=year)
    cat2_seq, _ = NumberSequence.objects.get_or_create(kind=NumberSequence.CERT_CATEGORY_II, year=year)

    def highest_issued(kind):
        code = settings_obj.listing_certificate_code if kind == NumberSequence.CERT_LISTING else settings_obj.category_ii_certificate_code
        prefix = f"TZ{str(year)[2:]}{code}"
        highest = 0
        for number in MedicineApplication.all_objects.filter(certificate_number__startswith=prefix).values_list('certificate_number', flat=True):
            match = services.CERT_PATTERN.match(number)
            if match and match.group(2) == code:
                highest = max(highest, int(match.group(3)))
        return highest

    settings_form = SystemSettingsForm(instance=settings_obj)
    counter_form = CounterForm(initial={'listing_last_number': listing_seq.last_number, 'category_ii_last_number': cat2_seq.last_number})

    if request.method == 'POST' and request.POST.get('form') == 'settings':
        settings_form = SystemSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if settings_form.is_valid():
            settings_form.save()
            messages.success(request, 'Settings saved.')
            return redirect('medicines:system_settings')
    elif request.POST.get('form') == 'counters':
        counter_form = CounterForm(request.POST)
        if counter_form.is_valid():
            problems = []
            for seq, field in ((listing_seq, 'listing_last_number'), (cat2_seq, 'category_ii_last_number')):
                value = counter_form.cleaned_data[field]
                floor = highest_issued(seq.kind)
                if value < floor:
                    problems.append(f"{seq.get_kind_display()} cannot go below {floor}, the highest number already issued this year.")
                    continue
                seq.last_number = value
                seq.save(update_fields=['last_number', 'updated_at'])
            for problem in problems:
                messages.error(request, problem)
            if not problems:
                messages.success(request, f'Counters for {year} saved.')
            return redirect('medicines:system_settings')

    return render(request, 'medicines/staff/system_settings.html', {
        'settings_form': settings_form,
        'counter_form': counter_form,
        'year': year,
        'next_listing': f"TZ{str(year)[2:]}{settings_obj.listing_certificate_code}{listing_seq.last_number + 1:0{settings_obj.certificate_digits}d}",
        'next_category_ii': f"TZ{str(year)[2:]}{settings_obj.category_ii_certificate_code}{cat2_seq.last_number + 1:0{settings_obj.certificate_digits}d}",
        'settings_obj': settings_obj,
    })
