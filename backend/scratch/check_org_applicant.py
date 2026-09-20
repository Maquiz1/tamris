import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models.profiles import Organization
from django.db import IntegrityError

org = Organization.objects.last()
print(org.organization_name)
