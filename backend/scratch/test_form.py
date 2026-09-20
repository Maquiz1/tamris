import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.forms.profiles import ApplicantAddressFormSet, OrganizationRepresentativeFormSet
print(ApplicantAddressFormSet().prefix)
print(OrganizationRepresentativeFormSet().prefix)
