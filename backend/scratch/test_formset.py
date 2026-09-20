import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models.profiles import Organization
from users.forms.profiles import ApplicantAddressFormSet, OrganizationRepresentativeFormSet

org = Organization.objects.last()
print("Organization:", org)

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
}

addr_fs = ApplicantAddressFormSet(data, instance=org.applicant)
print("Address Valid?", addr_fs.is_valid())
if not addr_fs.is_valid():
    print("Address Errors:", addr_fs.errors)

rep_fs = OrganizationRepresentativeFormSet(data, instance=org)
print("Rep Valid?", rep_fs.is_valid())
if not rep_fs.is_valid():
    print("Rep Errors:", rep_fs.errors)
