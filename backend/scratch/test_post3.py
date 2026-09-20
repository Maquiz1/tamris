import os
import sys
import django
from django.http import QueryDict

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

q = QueryDict('', mutable=True)
q.appendlist('addresses-TOTAL_FORMS', '1')
q.appendlist('addresses-TOTAL_FORMS', '1')

print("get:", q.get('addresses-TOTAL_FORMS'))
print("getlist:", q.getlist('addresses-TOTAL_FORMS'))

from users.forms.profiles import ApplicantAddressFormSet
from users.models.profiles import Organization
org = Organization.objects.last()

q.update({
    'addresses-INITIAL_FORMS': '0',
    'addresses-MIN_NUM_FORMS': '0',
    'addresses-MAX_NUM_FORMS': '1000',
    'addresses-0-country': 'Tanzania',
})
q.appendlist('addresses-INITIAL_FORMS', '0')
q.appendlist('addresses-MIN_NUM_FORMS', '0')
q.appendlist('addresses-MAX_NUM_FORMS', '1000')

fs = ApplicantAddressFormSet(q, instance=org.applicant)
print("valid?", fs.is_valid())
print("errors:", fs.errors)
print("non_form_errors:", fs.non_form_errors())

