import os

def user_document_path(instance, filename):
    """
    Generate file path for user profile documents.
    Format: users/user_<user_id>/<filename>
    """
    user_id = instance.user.id if instance.user else 'unknown'
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
