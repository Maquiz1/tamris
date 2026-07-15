from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser

def send_tamris_email(subject, message, recipient_list):
    """
    Wrapper for Django's send_mail function with standard TAMRIS sender.
    """
    if not recipient_list:
        return
        
    print(f"DEBUG EMAIL - Subject: {subject} | To: {recipient_list}")
    
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
    staff_users = CustomUser.objects.filter(
        role__name__in=['Admin', 'Evaluator'],
        is_active=True
    )
    staff_emails = list(staff_users.values_list('email', flat=True))
    
    if not staff_emails:
        return
        
    subject = "TAMRIS - New Applicant Registration Pending Review"
    message = (
        f"Hello,\n\n"
        f"A new applicant ({applicant.email}) has completed their onboarding profile and is pending verification.\n"
        f"Please log in to the TAMRIS portal to review their documents.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    send_tamris_email(subject, message, staff_emails)

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
    finance_users = CustomUser.objects.filter(
        role__name__in=['Admin', 'Accountant'],
        is_active=True
    )
    finance_emails = list(finance_users.values_list('email', flat=True))
    
    if not finance_emails:
        return
        
    subject = f"TAMRIS - New Payment Receipt Submitted ({payment.get_payment_type_display()})"
    message = (
        f"Hello,\n\n"
        f"Applicant {applicant.email} has submitted a receipt number for {payment.get_payment_type_display()}.\n"
        f"Receipt Number: {payment.receipt_number}\n"
        f"Amount Due: {payment.amount} TZS\n\n"
        f"Please log in to the TAMRIS portal to verify this payment.\n\n"
        f"Thank you,\nTAMRIS System"
    )
    
    send_tamris_email(subject, message, finance_emails)

def notify_evaluator_payment_verified(application, payment_type):
    """
    Notify Evaluators that a payment has been verified and the application is ready for the next step.
    """
    evaluators = CustomUser.objects.filter(
        role__name__in=['Admin', 'Evaluator'],
        is_active=True
    )
    evaluator_emails = list(evaluators.values_list('email', flat=True))
    
    if not evaluator_emails:
        return
        
    subject = f"TAMRIS - Payment Verified for {application.medicine_name}"
    
    if payment_type == 'EVALUATION_FEE':
        next_step = "Preliminary Screening"
    elif payment_type == 'LISTING_FEE':
        next_step = "Granting Full Registration"
    else:
        next_step = "Evaluation"
        
    message = (
        f"Hello,\n\n"
        f"The {payment_type.replace('_', ' ').title()} for the application '{application.medicine_name}' has been verified by Finance.\n"
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
