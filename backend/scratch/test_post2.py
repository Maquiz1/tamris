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
    
    data = {
        'addresses-TOTAL_FORMS': '1',
        'addresses-INITIAL_FORMS': '0',
        'addresses-MIN_NUM_FORMS': '0',
        'addresses-MAX_NUM_FORMS': '1000',
        'addresses-0-country': 'Tanzania',
        
        'representatives-TOTAL_FORMS': '1',
        'representatives-INITIAL_FORMS': '0',
        'representatives-MIN_NUM_FORMS': '0',
        'representatives-MAX_NUM_FORMS': '1000',
        'representatives-0-first_name': 'Test',
        'representatives-0-last_name': 'Test',
        'representatives-0-position': 'CEO',
        
        'contact-mobile_phone': '0700000000',
        'contact-email': 'test@test.com',
        
        'organization_name': 'Company X',
    }
    
    response = c.post('/onboarding/?step=2', data=data)
    html = response.content.decode()
    if 'TOTAL_FORMS' in html:
        print("Validation errors exist:")
        for line in html.split('\n'):
            if 'This field is required' in line or 'TOTAL_FORMS' in line:
                print(line.strip())
    else:
        print("Success! Redirected to step 3?")
        print("Response status:", response.status_code)
