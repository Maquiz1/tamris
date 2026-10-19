"""
Records that existed on paper before TAMRIS (System Flow v7, section 11).

A Data Clerk enters applicants and completed medicines. Applicants and rejected
records are saved straight away; a certificate waits for a Registrar to check it
against the scan. Applicants are linked by invitation, or by claiming the records
when they register on their own.
"""
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from medicines import services
from medicines.models import MedicineApplication, Payment
from users import emails
from users.models import (
    CustomUser, Role, Applicant, Individual, Organization, ApplicantIdentity,
    ApplicantAddress, ApplicantContact, OrganizationRepresentative, ApplicantDocument, LegacyClaim,
)

APPLICANT_DOCUMENT_FIELDS = ['nida_copy', 'tahpc_certificate', 'brela_certificate', 'tin_certificate', 'business_license']


@transaction.atomic
def create_legacy_applicant(data, files, clerk):
    """Create an applicant account from paper records. It is treated as already verified."""
    is_company = data['applicant_type'] == 'Organization'
    role = Role.objects.get(name='Company Applicant' if is_company else 'Individual Applicant')
    user = CustomUser(
        email=data['email'],
        phone_number=data.get('phone_number') or None,
        role=role,
        is_email_verified=True,
        is_onboarding_complete=True,
        registration_status='VERIFIED',
        is_legacy=True,
        created_by=clerk,
    )
    user.set_unusable_password()
    user.save()

    applicant = Applicant.objects.create(user=user, applicant_type=data['applicant_type'], status='Verified', created_by=clerk)
    if is_company:
        org = Organization.objects.create(
            applicant=applicant,
            organization_name=data['organization_name'],
            registration_number=data.get('registration_number') or None,
            tin=data.get('tin'),
        )
        if data.get('representative_name'):
            parts = data['representative_name'].split()
            OrganizationRepresentative.objects.create(
                organization=org, first_name=parts[0], last_name=' '.join(parts[1:]) or parts[0], is_primary=True,
            )
    else:
        Individual.objects.create(
            applicant=applicant,
            first_name=data['first_name'],
            middle_name=data.get('middle_name') or None,
            last_name=data['last_name'],
            tin=data.get('tin'),
        )
        ApplicantIdentity.objects.create(
            applicant=applicant,
            identity_type=data.get('identity_type') or 'NIDA (National ID)',
            identity_number=data['identity_number'],
            is_primary=True,
        )
    ApplicantContact.objects.create(applicant=applicant, mobile_phone=data.get('phone_number') or '', email=data['email'])
    if data.get('region') or data.get('district') or data.get('postal_address'):
        ApplicantAddress.objects.create(
            applicant=applicant, region=data.get('region'), district=data.get('district'), postal_address=data.get('postal_address'),
        )
    for field in APPLICANT_DOCUMENT_FIELDS:
        if files.get(field):
            ApplicantDocument.objects.create(applicant=applicant, document_type=field, file=files[field])
    return user


@transaction.atomic
def save_legacy_medicine(form, payment_formset, clerk):
    """Save (or correct) a paper record. Certificates go to the Registrar; rejected records are final."""
    app = form.save(commit=False)
    is_new = app.pk is None
    app.is_legacy = True
    app.legacy_entered_by = app.legacy_entered_by or clerk
    if form.cleaned_data['outcome'] == 'CERTIFIED':
        app.status = 'FULL_REGISTRATION'
        app.legacy_verification_status = 'PENDING'
        app.legacy_return_reason = None
    else:
        app.status = 'REJECTED'
        app.legacy_verification_status = None
    app.submitted_at = app.submitted_at or timezone.now()
    app.save()
    services.assign_reference(app)
    if app.certificate_number:
        services.register_paper_number(app.certificate_number)

    if payment_formset is not None:
        for row in payment_formset.cleaned_data:
            if not row or not row.get('payment_type'):
                continue
            amount = row.get('amount')
            Payment.objects.create(
                application=app,
                payment_type=row['payment_type'],
                amount=amount or 0,
                amount_paid=amount,
                receipt_number=None,
                remarks=f"Paid before the system. Receipt: {row.get('receipt_number') or '-'}"
                        + ('' if amount is not None else '. Amount not verified.'),
                is_verified=True,
                verified_at=timezone.now(),
                paid_before_system=True,
                created_by=clerk,
            )

    if app.status == 'FULL_REGISTRATION':
        emails.notify_registrars_legacy_entered(app, is_new)
    else:
        maybe_invite(app.applicant)
    return app


def legacy_pending_queryset():
    return MedicineApplication.objects.filter(is_legacy=True, is_void=False, status='FULL_REGISTRATION', legacy_verification_status='PENDING')


@transaction.atomic
def verify_legacy_certificate(application, registrar):
    if application.legacy_verification_status != 'PENDING':
        raise services.WorkflowError('This record is not waiting for verification.')
    if application.legacy_entered_by_id == registrar.id:
        raise services.WorkflowError('You entered this record, so another Registrar has to verify it.')
    application.legacy_verification_status = 'VERIFIED'
    application.legacy_verified_by = registrar
    application.legacy_verified_at = timezone.now()
    application.final_approved_by = registrar
    application.final_approved_at = application.final_approved_at or timezone.now()
    application.save()
    maybe_invite(application.applicant)


@transaction.atomic
def return_legacy_record(application, registrar, reason):
    if application.legacy_verification_status != 'PENDING':
        raise services.WorkflowError('This record is not waiting for verification.')
    if not reason:
        raise services.WorkflowError('Say what the Data Clerk must correct.')
    application.legacy_verification_status = 'RETURNED'
    application.legacy_return_reason = reason
    application.save()
    emails.notify_clerk_legacy_returned(application)


@transaction.atomic
def void_legacy_record(application, user, reason):
    if not application.is_legacy:
        raise services.WorkflowError('Only legacy records can be voided here.')
    if not reason:
        raise services.WorkflowError('Give the reason the record is void.')
    application.is_void = True
    application.void_reason = reason
    # Free the number so the correct record can use it; keep it in the reason for the history.
    if application.certificate_number:
        application.void_reason = f"{reason} (certificate number was {application.certificate_number})"
        application.certificate_number = None
    application.updated_by = user
    application.save()


def maybe_invite(user):
    """Invite a legacy applicant once, after their first record becomes visible."""
    if not user.is_legacy or user.legacy_invited_at or user.has_usable_password() or not user.email:
        return False
    emails.send_legacy_invitation(user)
    return True


# ── Claims ───────────────────────────────────────────────────────────────────

def find_legacy_matches(user):
    """Legacy profiles (never activated) whose ID, TIN or BRELA number matches this user's profile."""
    profile = getattr(user, 'applicant_profile', None)
    if profile is None or user.is_legacy:
        return []
    ids = list(profile.identities.exclude(identity_number='').values_list('identity_number', flat=True))
    tins, regs = [], []
    if hasattr(profile, 'individual') and profile.individual.tin:
        tins.append(profile.individual.tin)
    if hasattr(profile, 'organization'):
        if profile.organization.tin:
            tins.append(profile.organization.tin)
        if profile.organization.registration_number:
            regs.append(profile.organization.registration_number)
    if not (ids or tins or regs):
        return []

    match_q = Q(pk__in=[])
    if ids:
        match_q |= Q(applicant_profile__identities__identity_number__in=ids)
    if tins:
        match_q |= Q(applicant_profile__individual__tin__in=tins) | Q(applicant_profile__organization__tin__in=tins)
    if regs:
        match_q |= Q(applicant_profile__organization__registration_number__in=regs)

    already = LegacyClaim.objects.filter(new_user=user, status__in=['PENDING', 'CONFIRMED']).values_list('legacy_user_id', flat=True)
    candidates = CustomUser.objects.filter(match_q, is_legacy=True, is_active=True).exclude(pk=user.pk).exclude(pk__in=already).distinct()
    return [c for c in candidates if not c.has_usable_password()]


def describe_match(user, legacy_user):
    profile, legacy_profile = user.applicant_profile, legacy_user.applicant_profile
    ids = set(profile.identities.values_list('identity_number', flat=True)) & set(legacy_profile.identities.values_list('identity_number', flat=True))
    if ids:
        return f"ID number {ids.pop()}"
    for attr in ('individual', 'organization'):
        mine, theirs = getattr(profile, attr, None), getattr(legacy_profile, attr, None)
        if mine and theirs and mine.tin and mine.tin == theirs.tin:
            return f"TIN {mine.tin}"
    if hasattr(profile, 'organization') and hasattr(legacy_profile, 'organization'):
        return f"BRELA number {profile.organization.registration_number}"
    return 'matching details'


def request_claim(user, legacy_user):
    if legacy_user not in find_legacy_matches(user):
        raise services.WorkflowError('These records do not match your profile.')
    claim = LegacyClaim.objects.create(new_user=user, legacy_user=legacy_user, matched_on=describe_match(user, legacy_user))
    emails.notify_staff_claim_requested(claim)
    return claim


@transaction.atomic
def confirm_claim(claim, staff_user, note=''):
    if claim.status != 'PENDING':
        raise services.WorkflowError('This request has already been decided.')
    MedicineApplication.all_objects.filter(applicant=claim.legacy_user).update(applicant=claim.new_user)
    legacy_user = claim.legacy_user
    legacy_user.is_active = False
    legacy_user.save(update_fields=['is_active'])
    claim.status = 'CONFIRMED'
    claim.decided_by = staff_user
    claim.decided_at = timezone.now()
    claim.decision_note = note
    claim.save()
    emails.send_tamris_email(
        'TAMRIS - Your earlier records are now linked',
        'Hello,\n\nThe Council has confirmed your request. The medicines recorded before TAMRIS are now in your account.\n\n'
        'Thank you,\nTAMRIS System',
        [claim.new_user.email],
    )


@transaction.atomic
def reject_claim(claim, staff_user, note):
    if claim.status != 'PENDING':
        raise services.WorkflowError('This request has already been decided.')
    if not note:
        raise services.WorkflowError('Give the reason, so the applicant knows why.')
    claim.status = 'REJECTED'
    claim.decided_by = staff_user
    claim.decided_at = timezone.now()
    claim.decision_note = note
    claim.save()
    emails.send_tamris_email(
        'TAMRIS - Request to link earlier records',
        f'Hello,\n\nThe Council could not confirm your request to link earlier records.\nReason: {note}\n\nThank you,\nTAMRIS System',
        [claim.new_user.email],
    )
