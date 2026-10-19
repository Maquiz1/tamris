"""
Freeze the numbers the system already shows, before switching to stored numbers.

Until now the certificate number was computed on every page load as
TZ + (year of last update) + TM + (record id), and provisional letters showed
TAHPC/PROV/ + (record id). This migration stores those values exactly as they
were last printed, gives every application a reference number, and sets each
counter past the numbers already in use.

Safe to run more than once: it only fills fields that are still empty.
"""
import re

from django.db import migrations
from django.utils import timezone

# For the current year the counters start after the numbers already used on paper.
# TAHPC decision (System Flow v7): assume 200 until the administrator adjusts it.
PAPER_NUMBERS_ALREADY_USED = 200

PROVISIONAL_STATUSES = ['PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE', 'PENDING_FINAL_APPROVAL', 'PROVISIONAL_REGISTRATION']
CERT_PATTERN = re.compile(r'^TZ(\d{2})([A-Z]+)(\d+)$')


def add_one_year(day):
    try:
        return day.replace(year=day.year + 1)
    except ValueError:  # 29 February
        return day.replace(year=day.year + 1, day=28)


def forwards(apps, schema_editor):
    MedicineApplication = apps.get_model('medicines', 'MedicineApplication')
    NumberSequence = apps.get_model('medicines', 'NumberSequence')
    SystemSettings = apps.get_model('medicines', 'SystemSettings')

    if not SystemSettings.objects.exists():
        SystemSettings.objects.create(
            mandatory_listing_documents=['sample_label', 'ingredients_info_doc'],
            mandatory_category_ii_documents=['scientific_name_report'],
            mandatory_individual_documents=[],
            mandatory_company_documents=['brela_certificate', 'tin_certificate', 'business_license'],
        )

    applications = MedicineApplication.objects.all().order_by('created_at', 'id')

    # 1. Application references, numbered per service and per year in creation order
    ref_counters = {}
    for app in applications:
        kind = 'REF_LISTING' if app.application_type == 'LISTING' else 'REF_CATEGORY_II'
        year = timezone.localtime(app.created_at).year
        if app.reference_number:
            continue
        ref_counters[(kind, year)] = ref_counters.get((kind, year), 0) + 1
        code = 'LST' if kind == 'REF_LISTING' else 'REG'
        app.reference_number = f"TAHPC/{code}/{year}/{ref_counters[(kind, year)]:04d}"
        app.save(update_fields=['reference_number'])

    for (kind, year), last in ref_counters.items():
        seq, _ = NumberSequence.objects.get_or_create(kind=kind, year=year)
        if last > seq.last_number:
            seq.last_number = last
            seq.save(update_fields=['last_number'])

    # 2. Provisional letters already printed: keep their old reference and date
    for app in applications.filter(status__in=PROVISIONAL_STATUSES):
        changed = []
        if not app.former_reference:
            app.former_reference = f"TAHPC/PROV/{app.id:06d}"
            changed.append('former_reference')
        if not app.provisional_issued_on:
            app.provisional_issued_on = timezone.localtime(app.updated_at).date()
            changed.append('provisional_issued_on')
        if changed:
            app.save(update_fields=changed)

    # 3. Certificates already issued: store the number and date exactly as printed
    for app in applications.filter(status='FULL_REGISTRATION', is_legacy=False):
        if app.certificate_number:
            continue
        printed_year = app.updated_at.strftime('%y')
        issued_on = timezone.localtime(app.updated_at).date()
        app.certificate_number = f"TZ{printed_year}TM{app.id:04d}"
        app.certificate_issued_on = issued_on
        app.certificate_expires_on = add_one_year(issued_on)
        app.final_approved_at = app.updated_at
        app.former_reference = app.former_reference or f"TAHPC/PROV/{app.id:06d}"
        app.save(update_fields=['certificate_number', 'certificate_issued_on', 'certificate_expires_on', 'final_approved_at', 'former_reference'])

    # 4. Certificate counters: past every number in use, and past the paper range this year
    highest = {}
    for number in MedicineApplication.objects.exclude(certificate_number__isnull=True).values_list('certificate_number', flat=True):
        match = CERT_PATTERN.match(number or '')
        if not match:
            continue
        year = 2000 + int(match.group(1))
        code = match.group(2)
        kinds = ['CERT_LISTING'] if code == 'TL' else ['CERT_CATEGORY_II']
        for kind in kinds:
            highest[(kind, year)] = max(highest.get((kind, year), 0), int(match.group(3)))

    this_year = timezone.localdate().year
    for kind in ('CERT_LISTING', 'CERT_CATEGORY_II'):
        highest[(kind, this_year)] = max(highest.get((kind, this_year), 0), PAPER_NUMBERS_ALREADY_USED)

    for (kind, year), last in highest.items():
        seq, _ = NumberSequence.objects.get_or_create(kind=kind, year=year)
        if last > seq.last_number:
            seq.last_number = last
            seq.save(update_fields=['last_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('medicines', '0029_systemsettings_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
