from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from .models import CustomUser


def staff_emails(roles):
    """Emails of active users holding any of the roles, as main or additional role."""
    users = CustomUser.objects.filter(
        Q(role__name__in=roles) | Q(additional_roles__name__in=roles),
        is_active=True,
    ).distinct()
    return list(users.values_list('email', flat=True))

def send_tamris_email(subject, message, recipient_list):
    """
    Wrapper for Django's send_mail function with standard TAMRIS sender.
    """
    if not recipient_list:
        return
        
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@tamris.go.tz'),
        recipient_list=recipient_list,
        fail_silently=True,
    )

def notify_staff_new_registration(applicant):
    """
    Notify Admins and Evaluators that a new applicant has submitted their profile for review.
    """
    recipients = staff_emails(['Admin', 'Evaluator'])
    
    if not recipients:
        return
        
    subject = "TAMRIS - New Applicant Registration Pending Review"
    message = (
        f"Hello,\n\n"
        f"A new applicant ({applicant.email}) has completed their onboarding profile and is pending verification.\n"
        f"Please log in to the TAMRIS portal to review their documents.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    send_tamris_email(subject, message, recipients)

def notify_applicant_registration_status(applicant, status, reason=None):
    """
    Notify the applicant about their registration review outcome.
    """
    if status == 'VERIFIED':
        subject = "TAMRIS - Registration Verified"
        message = (
            f"Hello,\n\n"
            f"Congratulations! Your registration profile has been verified successfully.\n"
            f"You can now log in to the TAMRIS portal to submit your medicine applications.\n\n"
            f"Thank you,\nTAMRIS System"
        )
    else:
        subject = "TAMRIS - Registration Rejected"
        message = (
            f"Hello,\n\n"
            f"Unfortunately, your registration profile has been rejected.\n"
            f"Reason: {reason}\n\n"
            f"Please log in to the TAMRIS portal to correct the issues and resubmit.\n\n"
            f"Thank you,\nTAMRIS System"
        )
        
    send_tamris_email(subject, message, [applicant.email])

def notify_finance_pending_payment(payment, applicant):
    """
    Notify Accountants/Admins that a new payment receipt has been submitted.
    """
    finance_emails = staff_emails(['Admin', 'Accountant'])
    
    if not finance_emails:
        return
        
    subject = f"TAMRIS - New Payment Receipt Submitted ({payment.get_payment_type_display()})"
    message = (
        f"Hello,\n\n"
        f"Applicant {applicant.email} has submitted payment details for {payment.get_payment_type_display()}.\n"
        f"Application: {payment.application.reference_number or payment.application.medicine_name}\n"
        f"Control Number: {payment.control_number}\n"
        f"Receipt Number: {payment.receipt_number or '-'}\n"
        f"Amount Due: {payment.amount} TZS\n\n"
        f"Please log in to the TAMRIS portal to verify this payment.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    send_tamris_email(subject, message, finance_emails)

def notify_evaluator_payment_verified(application, payment_type):
    """
    Notify Evaluators that a payment has been verified and the application is ready for the next step.
    """
    evaluator_emails = staff_emails(['Admin', 'Evaluator'])
    
    if not evaluator_emails:
        return
        
    subject = f"TAMRIS - Payment Verified for {application.medicine_name}"
    
    from medicines.models import Payment
    fee_name = dict(Payment._meta.get_field('payment_type').choices).get(payment_type, payment_type)
    if payment_type in ('LISTING_EVAL_FEE', 'CAT_II_EVAL_FEE'):
        next_step = "Preliminary Screening"
    elif payment_type == 'CAT_II_INSPECTION_FEE':
        next_step = "Inspection Scheduling"
    else:
        next_step = "the next evaluation step"
        
    message = (
        f"Hello,\n\n"
        f"The {fee_name} for the application '{application.medicine_name}' ({application.reference_number or '-'}) has been verified by Finance.\n"
        f"The application is now ready for {next_step}.\n\n"
        f"Please log in to the TAMRIS portal to proceed.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    send_tamris_email(subject, message, evaluator_emails)

def notify_applicant_application_status(application, subject, body_text):
    """
    Notify the applicant about updates to their medicine application.
    """
    message = (
        f"Hello,\n\n"
        f"There is an update regarding your application for '{application.medicine_name}'.\n\n"
        f"{body_text}\n\n"
        f"Please log in to the TAMRIS portal to view more details.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    send_tamris_email(subject, message, [application.applicant.email])

def notify_staff_account_created(user, temp_password, otp_code):
    """
    Notify a newly created staff member with their temporary credentials.
    """
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    login_url = f"{site_url}/login/"
    
    subject = "TAMRIS - Your Staff Account Has Been Created"
    message = (
        f"Hello,\n\n"
        f"An administrator has created a TAMRIS staff account for you.\n\n"
        f"Login Link: {login_url}\n"
        f"Login Email: {user.email}\n"
        f"Temporary Password: {temp_password}\n\n"
        f"To complete your registration, please click the link above, log in with these credentials, and enter the following verification code:\n"
        f"Verification Code: {otp_code}\n\n"
        f"This code will expire in 5 minutes.\n\n"
        f"Once verified, an administrator will assign your specific system roles.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    send_tamris_email(subject, message, [user.email])

def notify_inspection_scheduled(application, schedule):
    inspector_emails = [inspector.email for inspector in schedule.assigned_inspectors.all() if inspector.email]
    applicant_email = application.applicant.email
    
    subject = f"TAMRIS - Inspection Scheduled for {application.medicine_name}"
    
    checklist = []
    if schedule.check_manufacturing_area: checklist.append("• Eneo la uzalishaji (Manufacturing area)")
    if schedule.check_machines: checklist.append("• Mashine (Machines)")
    if schedule.check_cleanliness: checklist.append("• Usafi (Cleanliness)")
    if schedule.check_medicine_storage: checklist.append("• Hifadhi ya dawa (Medicine storage)")
    if schedule.check_quality_control: checklist.append("• Mfumo wa udhibiti wa ubora (Quality control system)")
    
    checklist_text = "\n".join(checklist) if checklist else "N/A"
    
    inspector_message = (
        f"Hello,\n\n"
        f"An inspection for the medicine '{application.medicine_name}' has been scheduled.\n\n"
        f"Start: {schedule.start_date_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"End: {schedule.end_date_time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"HATUA YA 5: UKAGUZI WA ENEO LA UZALISHAJI (STEP 5: INSPECTION OF MANUFACTURING SITE)\n"
        f"Ukaguzi utahusisha (The inspection shall involve):\n"
        f"{checklist_text}\n\n"
    )
    if schedule.evaluator_remarks_for_inspectors:
        inspector_message += f"Evaluator Remarks:\n{schedule.evaluator_remarks_for_inspectors}\n\n"
    inspector_message += f"Thank you,\nTAMRIS System"

    applicant_message = (
        f"Hello,\n\n"
        f"An inspection for the medicine '{application.medicine_name}' has been scheduled.\n\n"
        f"Start: {schedule.start_date_time.strftime('%Y-%m-%d %H:%M')}\n"
        f"End: {schedule.end_date_time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"HATUA YA 5: UKAGUZI WA ENEO LA UZALISHAJI (STEP 5: INSPECTION OF MANUFACTURING SITE)\n"
        f"Ukaguzi utahusisha (The inspection shall involve):\n"
        f"{checklist_text}\n\n"
    )
    if schedule.evaluator_remarks_for_applicant:
        applicant_message += f"Evaluator Remarks:\n{schedule.evaluator_remarks_for_applicant}\n\n"
    applicant_message += f"Thank you,\nTAMRIS System"
    
    if inspector_emails:
        send_tamris_email(subject, inspector_message, inspector_emails)
    if applicant_email:
        send_tamris_email(subject, applicant_message, [applicant_email])

def notify_ready_for_inspection(application):
    schedule = application.inspections.order_by('-created_at').first()
    inspector_emails = []
    if schedule:
        inspector_emails = [inspector.email for inspector in schedule.assigned_inspectors.all() if inspector.email]
    applicant_email = application.applicant.email
    all_emails = set(inspector_emails + [applicant_email])
    
    subject = f"TAMRIS - Ready for Inspection: {application.medicine_name}"
    message = (
        f"Hello,\n\n"
        f"The inspection fee for '{application.medicine_name}' has been verified by Finance.\n"
        f"The facility is now officially ready for inspection.\n\n"
        f"Inspectors can now log in to the TAMRIS portal to submit their inspection report.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    if all_emails:
        send_tamris_email(subject, message, list(all_emails))


def notify_registrars_ready_for_approval(application):
    recipients = staff_emails(['Registrar'])
    if not recipients:
        return
    send_tamris_email(
        f"TAMRIS - Ready for Final Approval: {application.medicine_name}",
        f"Hello,\n\nThe final fee for '{application.medicine_name}' ({application.reference_number or '-'}) has been verified.\n"
        f"The application is waiting for your approval on behalf of the Committee.\n\nThank you,\nTAMRIS System",
        recipients,
    )


def notify_registrars_number_clash(number, existing_application):
    recipients = staff_emails(['Registrar'])
    if not recipients:
        return
    send_tamris_email(
        f"TAMRIS - Certificate Number Clash: {number}",
        f"Hello,\n\nA Data Clerk tried to enter a paper certificate numbered {number}, but the system has already issued that "
        f"number to '{existing_application.medicine_name}' ({existing_application.reference_number or '-'}).\n"
        f"Please check the paper register and decide which record keeps the number.\n\nThank you,\nTAMRIS System",
        recipients,
    )


def notify_evaluators_resubmitted(application):
    recipients = staff_emails(['Admin', 'Evaluator'])
    if not recipients:
        return
    send_tamris_email(
        f"TAMRIS - Conditions Answered: {application.medicine_name}",
        f"Hello,\n\nThe applicant has corrected and resubmitted '{application.medicine_name}' ({application.reference_number or '-'}).\n"
        f"It is now at: {application.get_status_display()}.\n\nThank you,\nTAMRIS System",
        recipients,
    )


def notify_evaluators_inspection_report(schedule):
    recipients = staff_emails(['Admin', 'Evaluator'])
    if not recipients:
        return
    app = schedule.application
    result = 'GMP compliant' if schedule.gmp_compliant else 'NOT GMP compliant'
    send_tamris_email(
        f"TAMRIS - Inspection Report Submitted: {app.medicine_name}",
        f"Hello,\n\nThe inspection report for '{app.medicine_name}' ({app.reference_number or '-'}) has been submitted: {result}.\n"
        f"The application is ready for scientific evaluation.\n\nThank you,\nTAMRIS System",
        recipients,
    )


def notify_renewal_reminder(application, days_left):
    send_tamris_email(
        f"TAMRIS - Certificate {application.certificate_number} expires in {days_left} days",
        f"Hello,\n\nYour certificate {application.certificate_number} for '{application.medicine_name}' expires on "
        f"{application.certificate_expires_on:%d %B %Y}.\nPlease log in to TAMRIS and renew it by paying the renewal fee.\n\n"
        f"Thank you,\nTAMRIS System",
        [application.applicant.email],
    )


def notify_certificate_expired(application):
    send_tamris_email(
        f"TAMRIS - Certificate {application.certificate_number} has expired",
        f"Hello,\n\nYour certificate {application.certificate_number} for '{application.medicine_name}' expired on "
        f"{application.certificate_expires_on:%d %B %Y}.\nYou can still renew it in TAMRIS by paying the renewal fee.\n\n"
        f"Thank you,\nTAMRIS System",
        [application.applicant.email],
    )
    recipients = staff_emails(['Evaluator'])
    if recipients:
        send_tamris_email(
            f"TAMRIS - Certificate expired: {application.certificate_number}",
            f"The certificate {application.certificate_number} for '{application.medicine_name}' expired on "
            f"{application.certificate_expires_on:%d %B %Y} and has not been renewed.",
            recipients,
        )


def send_legacy_invitation(user):
    """Invite an applicant entered from paper records to set a password."""
    from django.contrib.auth.tokens import default_token_generator
    from django.urls import reverse
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode
    from django.utils import timezone

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = site_url + reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    send_tamris_email(
        "TAMRIS - Your medicines are now in the TAMRIS portal",
        f"Hello,\n\nThe Traditional and Alternative Health Practice Council has moved your records into the TAMRIS online portal.\n"
        f"Set your password with this link to see your medicines and certificates, renew them and make new applications:\n{link}\n\n"
        f"Your login email is {user.email}.\n\nThank you,\nTAMRIS System",
        [user.email],
    )
    user.legacy_invited_at = timezone.now()
    user.save(update_fields=['legacy_invited_at'])


def notify_registrars_legacy_entered(application, is_new):
    recipients = [e for e in staff_emails(['Registrar']) if not application.legacy_entered_by or e != application.legacy_entered_by.email]
    if not recipients:
        return
    action = 'entered' if is_new else 'corrected'
    send_tamris_email(
        f"TAMRIS - Legacy certificate to verify: {application.certificate_number}",
        f"Hello,\n\nA Data Clerk has {action} the paper certificate {application.certificate_number} for '{application.medicine_name}'.\n"
        f"Please compare it with the scan and verify it, or return it for correction.\n\nThank you,\nTAMRIS System",
        recipients,
    )


def notify_clerk_legacy_returned(application):
    clerk = application.legacy_entered_by
    if not clerk or not clerk.email:
        return
    send_tamris_email(
        f"TAMRIS - Legacy record returned: {application.medicine_name}",
        f"Hello,\n\nThe Registrar returned the legacy record '{application.medicine_name}' ({application.certificate_number or '-'}) for correction.\n"
        f"Reason: {application.legacy_return_reason}\n\nThank you,\nTAMRIS System",
        [clerk.email],
    )


def notify_staff_claim_requested(claim):
    recipients = staff_emails(['Registrar', 'Admin'])
    if not recipients:
        return
    send_tamris_email(
        "TAMRIS - Request to link earlier records",
        f"Hello,\n\n{claim.new_user.email} has asked to link the records entered from paper for {claim.legacy_user.display_name}.\n"
        f"Matched on: {claim.matched_on}.\nPlease confirm or reject the request in TAMRIS.\n\nThank you,\nTAMRIS System",
        recipients,
    )
