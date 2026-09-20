import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tamris.settings')
django.setup()

from django.test import Client
from users.models import CustomUser

c = Client()
user = CustomUser.objects.filter(role__name='Company Applicant').first()
if user:
    c.force_login(user)
    response = c.get('/onboarding/?step=2')
    html = response.content.decode()
    for line in html.split('\n'):
        if 'TOTAL_FORMS' in line:
            print(line.strip())
else:
    print("No Company Applicant found.")
