import os
import sys
import django
import uuid

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models.profiles import Organization
orgs = Organization.objects.filter(organization_name='')
for i, org in enumerate(orgs):
    org.organization_name = f"Temp Org {uuid.uuid4()}"
    org.save()
