import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from users.models import (
    Applicant, Individual, Organization, ApplicantIdentity, 
    ApplicantAddress, ApplicantContact, Education, 
    OrganizationRepresentative, ApplicantDocument
)

models_to_create = [
    Applicant, Individual, Organization, ApplicantIdentity, 
    ApplicantAddress, ApplicantContact, Education, 
    OrganizationRepresentative, ApplicantDocument
]

with connection.schema_editor() as schema_editor:
    for model in models_to_create:
        try:
            schema_editor.create_model(model)
            print(f'Successfully created table for {model.__name__}')
        except Exception as e:
            print(f'Skipped {model.__name__}: {e}')
