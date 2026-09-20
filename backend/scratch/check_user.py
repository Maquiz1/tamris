import os
import sys
import django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from users.models import CustomUser
user = CustomUser.objects.filter(role__name='Company Applicant').first()
if user and hasattr(user, 'applicant_profile'):
    print(user.applicant_profile.organization.organization_name)
