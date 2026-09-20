from users.models import Applicant
from users.forms.profiles import ApplicantAddressFormSet

app = Applicant.objects.first()
if not app:
    print("No applicant")

data = {
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
    'addresses-0-postal_address': 'dar',
}

fset = ApplicantAddressFormSet(data, instance=app)
print("Is valid?", fset.is_valid())
if not fset.is_valid():
    print("Errors:", fset.errors)
    print("Non form errors:", fset.non_form_errors())
