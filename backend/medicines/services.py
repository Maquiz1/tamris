"""
Workflow rules for applications, payments, numbers and certificates.

Views call these functions instead of changing statuses themselves, so every
path (normal flow, legacy entry, renewal) follows the same rules.
"""
import re

from django.db import transaction
from django.utils import timezone

from medicines.models import MedicineApplication, NumberSequence, Payment, FeeConfiguration, SystemSettings
from users import emails


class WorkflowError(Exception):
    """An action that is not allowed in the application's current state."""


# ── Dates ────────────────────────────────────────────────────────────────────

def add_one_year(day):
    """Same date one year later (20 May 2026 -> 20 May 2027). 29 February becomes 28 February."""
    try:
        return day.replace(year=day.year + 1)
    except ValueError:
        return day.replace(year=day.year + 1, day=28)


# ── Numbers ──────────────────────────────────────────────────────────────────

CERT_PATTERN = re.compile(r'^TZ(\d{2})([A-Z]+)(\d+)$')


def _cert_kind(application_type):
    return NumberSequence.CERT_LISTING if application_type == 'LISTING' else NumberSequence.CERT_CATEGORY_II


def _cert_code(application_type, settings_obj=None):
    settings_obj = settings_obj or SystemSettings.load()
    if application_type == 'LISTING':
        return settings_obj.listing_certificate_code
    return settings_obj.category_ii_certificate_code


def assign_reference(application):
    """Give a new application its reference, e.g. TAHPC/LST/2026/0001."""
    if application.reference_number:
        return application.reference_number
    settings_obj = SystemSettings.load()
    year = timezone.localdate().year
    if application.application_type == 'LISTING':
        kind, code = NumberSequence.REF_LISTING, settings_obj.listing_reference_code
    else:
        kind, code = NumberSequence.REF_CATEGORY_II, settings_obj.category_ii_reference_code
    number = NumberSequence.take_next(kind, year)
    application.reference_number = f"{settings_obj.reference_prefix}/{code}/{year}/{number:04d}"
    application.save(update_fields=['reference_number'])
    return application.reference_number


def next_certificate_number(application_type, issued_on):
    settings_obj = SystemSettings.load()
    number = NumberSequence.take_next(_cert_kind(application_type), issued_on.year)
    code = _cert_code(application_type, settings_obj)
    return f"TZ{issued_on.strftime('%y')}{code}{number:0{settings_obj.certificate_digits}d}"


def validate_paper_certificate_number(number, application_type, exclude_pk=None):
    """
    Check a number typed from a paper certificate. Returns the cleaned number.
    Raises WorkflowError with a message the Data Clerk can act on.
    """
    number = (number or '').strip().upper().replace(' ', '')
    match = CERT_PATTERN.match(number)
    if not match:
        raise WorkflowError('Certificate number must look like TZ26TM0187: TZ, two-digit year, type code, then digits.')
    clash = MedicineApplication.all_objects.filter(certificate_number=number)
    if exclude_pk:
        clash = clash.exclude(pk=exclude_pk)
    clash = clash.first()
    if clash:
        if not clash.is_legacy:
            emails.notify_registrars_number_clash(number, clash)
        raise WorkflowError(f'Certificate number {number} is already used by {clash.medicine_name}. The Registrar has been alerted.' if not clash.is_legacy
                            else f'Certificate number {number} is already used by legacy record {clash.medicine_name}.')
    return number


def register_paper_number(number):
    """Move the counter for that year past a number taken from paper."""
    match = CERT_PATTERN.match(number)
    if not match:
        return
    settings_obj = SystemSettings.load()
    code = match.group(2)
    if code == settings_obj.listing_certificate_code:
        kind = NumberSequence.CERT_LISTING
    else:
        kind = NumberSequence.CERT_CATEGORY_II
    NumberSequence.ensure_at_least(kind, 2000 + int(match.group(1)), int(match.group(3)))


# ── Fees ─────────────────────────────────────────────────────────────────────

FEE_CODES = {
    'LISTING': {
        'application': 'LISTING_APP_FEE',
        'evaluation': 'LISTING_EVAL_FEE',
        'final': 'LISTING_FEE',
        'renewal': 'LISTING_RENEWAL_FEE',
    },
    'CATEGORY_II': {
        'application': 'CAT_II_APP_FEE',
        'evaluation': 'CAT_II_EVAL_FEE',
        'inspection': 'CAT_II_INSPECTION_FEE',
        'final': 'CAT_II_REGISTRATION_FEE',
        'renewal': 'CAT_II_RENEWAL_FEE',
    },
}

FALLBACK_AMOUNTS = {
    'LISTING_APP_FEE': 50000.0, 'CAT_II_APP_FEE': 100000.0,
    'LISTING_EVAL_FEE': 150000.0, 'CAT_II_EVAL_FEE': 300000.0,
    'CAT_II_INSPECTION_FEE': 150000.0,
    'LISTING_FEE': 200000.0, 'CAT_II_REGISTRATION_FEE': 200000.0,
}


def create_fee(application, stage):
    """Create the bill for a stage. Raises FeeInactiveError if that fee is switched off."""
    code = FEE_CODES[application.application_type][stage]
    amount = FeeConfiguration.get_fee(code, FALLBACK_AMOUNTS.get(code, 0.0))
    return Payment.objects.create(application=application, payment_type=code, amount=amount)


def has_fee(application, stage):
    code = FEE_CODES[application.application_type].get(stage)
    return bool(code) and application.payments.filter(payment_type=code).exists()


# ── Payments ─────────────────────────────────────────────────────────────────

@transaction.atomic
def verify_payment(payment, user, remarks=None):
    """Finance approves a payment. Moves the application to its next step."""
    if payment.is_verified:
        raise WorkflowError('This payment is already verified.')
    if not payment.control_number:
        raise WorkflowError('The applicant has not submitted a control number for this payment yet.')

    payment.is_verified = True
    payment.verified_by = user
    payment.verified_at = timezone.now()
    if remarks is not None:
        payment.remarks = remarks
    payment.save()

    app = payment.application
    code = payment.payment_type
    next_staff = None

    if code in ('LISTING_APP_FEE', 'CAT_II_APP_FEE') and app.status == 'PENDING_APPLICATION_FEE':
        app.status = 'DRAFT'
        message = 'Your application fee has been verified. You can now fill in the application form.'
    elif code in ('LISTING_EVAL_FEE', 'CAT_II_EVAL_FEE') and app.status == 'PENDING_EVALUATION_FEE':
        app.status = 'UNDER_REVIEW'
        message = 'Your evaluation fee has been verified. Your application is now in preliminary screening.'
        next_staff = 'evaluators'
    elif code == 'CAT_II_INSPECTION_FEE' and app.status in ('PENDING_INSPECTION_FEE', 'PRELIMINARY_APPROVED'):
        app.status = 'READY_FOR_INSPECTION'
        message = 'Your inspection fee has been verified. The Council will schedule the site inspection and notify you of the dates.'
        next_staff = 'evaluators'
    elif code in ('LISTING_FEE', 'CAT_II_REGISTRATION_FEE') and app.status in ('PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE', 'PROVISIONAL_REGISTRATION'):
        app.status = 'PENDING_FINAL_APPROVAL'
        message = 'Your fee has been verified. Your application is now waiting for final approval by the Registrar.'
        next_staff = 'registrars'
    elif code in Payment.RENEWAL_TYPES and app.status == 'FULL_REGISTRATION':
        renew_certificate(app)
        message = f'Your renewal fee has been verified. Your certificate {app.certificate_number} is now valid until {app.certificate_expires_on:%d %B %Y}.'
    else:
        message = 'Your payment has been verified.'

    app.save()
    emails.notify_applicant_application_status(app, f'TAMRIS - Payment Verified ({payment.get_payment_type_display()})', message)
    if next_staff == 'evaluators':
        emails.notify_evaluator_payment_verified(app, code)
    elif next_staff == 'registrars':
        emails.notify_registrars_ready_for_approval(app)
    return app


@transaction.atomic
def reject_payment(payment, user, reason):
    """Finance could not confirm the payment. The applicant must submit it again."""
    if payment.is_verified:
        raise WorkflowError('A verified payment cannot be reversed.')
    if not reason:
        raise WorkflowError('Please give the reason, so the applicant knows what to correct.')
    payment.control_number = None
    payment.receipt_number = None
    payment.reference_number = None
    payment.amount_paid = None
    payment.remarks = reason
    payment.updated_by = user
    payment.save()
    emails.notify_applicant_application_status(
        payment.application,
        'TAMRIS - Payment Not Confirmed',
        f'Finance could not confirm your {payment.get_payment_type_display()}.\nReason: {reason}\n'
        f'Please check the payment and submit the control number again.'
    )


# ── Evaluation outcomes ──────────────────────────────────────────────────────

@transaction.atomic
def apply_conditions(application, stage, comments, requires_reinspection=False):
    """Send named sections back to the applicant for correction."""
    if not comments:
        raise WorkflowError('Write the conditions in the comments so the applicant knows what to correct.')
    if stage == 'preliminary':
        return_status = 'UNDER_REVIEW'
    elif requires_reinspection and application.application_type == 'CATEGORY_II':
        return_status = 'READY_FOR_INSPECTION'
    else:
        return_status = application.status
    application.conditions_return_status = return_status
    application.status = 'CONDITIONS_APPLIED'
    application.review_remarks = comments
    application.save()
    extra = '\nAfter your corrections, an inspector will re-inspect the site. No new inspection fee is charged.' if return_status == 'READY_FOR_INSPECTION' else ''
    emails.notify_applicant_application_status(
        application,
        'TAMRIS - Conditions for Improvement',
        f'The Council has asked for corrections before your application can continue.\nConditions: {comments}{extra}\n'
        f'Please log in, correct the sections that are open for editing, and resubmit.'
    )


@transaction.atomic
def resubmit_after_conditions(application):
    application.status = application.conditions_return_status or 'UNDER_REVIEW'
    application.conditions_return_status = None
    application.submitted_at = timezone.now()
    application.save()
    emails.notify_evaluators_resubmitted(application)


@transaction.atomic
def give_provisional(application):
    """Scientific evaluation passed: provisional letter and the final fee."""
    payment = create_fee(application, 'final')
    application.status = 'PENDING_LISTING_FEE' if application.application_type == 'LISTING' else 'PENDING_REGISTRATION_FEE'
    application.provisional_issued_on = timezone.localdate()
    application.save()
    letter = 'Listing Provisional Letter' if application.application_type == 'LISTING' else 'Registration Provisional Letter'
    emails.notify_applicant_application_status(
        application,
        f'TAMRIS - {letter} Issued',
        f'Your application has passed scientific evaluation and your {letter} is ready to download.\n'
        f'Please pay the {payment.get_payment_type_display()} and submit the control number to proceed to the certificate.'
    )
    return payment


# ── Registrar approval and certificates ──────────────────────────────────────

@transaction.atomic
def issue_certificate(application, registrar):
    """The Registrar approves on behalf of the Committee. The certificate number is taken here, once."""
    application = MedicineApplication.objects.select_for_update().get(pk=application.pk)
    if application.status != 'PENDING_FINAL_APPROVAL':
        raise WorkflowError('Only applications whose final fee has been verified can be approved.')
    if application.certificate_number:
        raise WorkflowError('This application already has a certificate.')
    today = timezone.localdate()
    application.certificate_number = next_certificate_number(application.application_type, today)
    application.certificate_issued_on = today
    application.certificate_expires_on = add_one_year(today)
    application.final_approved_by = registrar
    application.final_approved_at = timezone.now()
    application.status = 'FULL_REGISTRATION'
    application.renewal_reminders_sent = []
    application.save()
    certificate = 'Listing Certificate' if application.application_type == 'LISTING' else 'Category II Registration Certificate'
    emails.notify_applicant_application_status(
        application,
        f'TAMRIS - {certificate} Issued',
        f'Congratulations! Your {certificate} {application.certificate_number} has been issued and is valid until '
        f'{application.certificate_expires_on:%d %B %Y}.\nYou can download it from the TAMRIS portal.'
    )
    return application


@transaction.atomic
def refuse_final_approval(application, registrar, reason):
    if application.status != 'PENDING_FINAL_APPROVAL':
        raise WorkflowError('Only applications waiting for final approval can be refused.')
    if not reason:
        raise WorkflowError('Please give the reason for refusing.')
    application.status = 'REJECTED'
    application.rejection_reason = reason
    application.final_approved_by = registrar
    application.final_approved_at = timezone.now()
    application.save()
    emails.notify_applicant_application_status(
        application, 'TAMRIS - Application Refused',
        f'The Registrar, on behalf of the Committee, has refused your application for {application.medicine_name}.\nReason: {reason}'
    )


def renew_certificate(application):
    """Extend a certificate by one year after its renewal fee is verified. Keeps the same number."""
    today = timezone.localdate()
    base = application.certificate_expires_on if application.certificate_expires_on and application.certificate_expires_on >= today else today
    application.certificate_expires_on = add_one_year(base)
    application.renewal_count += 1
    application.renewal_reminders_sent = []


def start_renewal(application):
    if not application.can_renew:
        raise WorkflowError('Renewal opens 90 days before the certificate expires.')
    return create_fee(application, 'renewal')


# ── Access to letters and certificates ───────────────────────────────────────

def can_view_certificate(user, application):
    if user.is_staff_member:
        return application.status == 'FULL_REGISTRATION' and bool(application.certificate_number)
    return application.applicant_id == user.id and application.has_active_certificate


def can_view_provisional(user, application):
    if application.is_legacy:
        return False
    if user.is_staff_member:
        return application.has_provisional_letter
    return application.applicant_id == user.id and application.provisional_letter_open_to_applicant
