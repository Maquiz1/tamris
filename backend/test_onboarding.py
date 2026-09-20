import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from users.views.onboarding import onboarding
from users.models import Role, Applicant, Organization, ApplicantAddress

User = get_user_model()
try:
    user = User.objects.get(email="baharidigital@gmail.com")
except User.DoesNotExist:
    # Just grab any user or exit
    user = User.objects.first()

if not user:
    print("No user found")
    exit()

factory = RequestFactory()
data = {
    # Organization form
    'organization_name': 'Bahari Digital',
    'organization_type': 'LLC',
    'registration_number': '12345678',
    'date_registered': '2023-01-01',
    'tin': '111222333',
    'year_established': '2023',
    
    # Address formset
    'addresses-TOTAL_FORMS': '1',
    'addresses-INITIAL_FORMS': '0',
    'addresses-MIN_NUM_FORMS': '0',
    'addresses-MAX_NUM_FORMS': '1000',
    'addresses-0-country': 'Tanzania',
    'addresses-0-region': 'Dar es Salaam',
    'addresses-0-district': 'Ilala',
    'addresses-0-ward': 'Kariakoo',
    'addresses-0-street': 'Mbezi Beach',
    'addresses-0-physical_address': 'Mbezi Beach',
    'addresses-0-postal_address': 'Dar',
    
    # Rep formset
    'representatives-TOTAL_FORMS': '1',
    'representatives-INITIAL_FORMS': '0',
    'representatives-MIN_NUM_FORMS': '0',
    'representatives-MAX_NUM_FORMS': '1000',
    'representatives-0-identity_type': 'NIDA (National ID)',
    'representatives-0-identity_number': '12345678901234567890',
    
    # Contact formset
    'contact-mobile_phone': '0712345678',
    'contact-email': 'baharidigital@gmail.com',
}

request = factory.post('/onboarding/2/', data)
request.user = user

# Call view
print("Testing view...")
response = onboarding(request, step=2)
print("Response status:", response.status_code)

if response.status_code == 302:
    print("Success! Redirected to", response.url)
    app = user.company_profile
    if app:
        print("Addresses count:", ApplicantAddress.objects.filter(applicant=app.applicant).count())
else:
    print("Failed. Form probably not valid.")
