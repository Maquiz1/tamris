import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from users.models import CustomUser

c = Client()
user = CustomUser.objects.filter(role__name='Company Applicant').first()
if user:
    c.force_login(user)
    
    # First get the page to get CSRF token and the management form data
    response = c.get('/onboarding/?step=2')
    html = response.content.decode()
    
    # Let's see if the management forms are even present in the HTML!
    found_rep = False
    found_addr = False
    for line in html.split('\n'):
        if 'representatives-TOTAL_FORMS' in line:
            found_rep = True
        if 'addresses-TOTAL_FORMS' in line:
            found_addr = True
    print(f"GET check: address_management_form present? {found_addr}")
    print(f"GET check: rep_management_form present? {found_rep}")
