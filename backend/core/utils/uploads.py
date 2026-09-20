import os

def user_document_path(instance, filename):
    """
    Generate file path for user profile documents.
    Format: users/user_<user_id>/<filename>
    """
    if hasattr(instance, 'user') and instance.user:
        user_id = instance.user.id
    elif hasattr(instance, 'applicant') and getattr(instance.applicant, 'user', None):
        user_id = instance.applicant.user.id
    else:
        user_id = 'unknown'
    return f'users/user_{user_id}/{filename}'

def medicine_document_path(instance, filename):
    """
    Generate file path for medicine application documents.
    Format: medicines/applications/user_<applicant_id>/<filename>
    """
    applicant_id = instance.applicant.id if instance.applicant else 'unknown'
    return f'medicines/applications/user_{applicant_id}/{filename}'

def inspection_document_path(instance, filename):
    """
    Generate file path for inspection reports.
    Format: medicines/inspections/app_<application_id>/<filename>
    """
    app_id = instance.application.id if instance.application else 'unknown'
    return f'medicines/inspections/app_{app_id}/{filename}'
