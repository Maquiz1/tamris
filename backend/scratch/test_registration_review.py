import os
import django
import sys
from django.test import Client
from django.urls import reverse

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import CustomUser

def test_evaluator_views():
    c = Client()
    # Find or create an admin/evaluator user
    admin_user = CustomUser.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No superuser found to test with.")
        return
        
    c.force_login(admin_user)
    
    list_url = reverse('users:staff_registration_list')
    print(f"Fetching {list_url}...")
    response = c.get(list_url)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"ERROR loading list view")
        return
        
    # Find an applicant user
    applicant = CustomUser.objects.filter(is_onboarding_complete=True, role__name__in=['Individual Applicant', 'Company Applicant']).first()
    if not applicant:
        print("No completed applicant found to test detail view.")
        return
        
    detail_url = reverse('users:staff_registration_detail', kwargs={'pk': applicant.pk})
    print(f"Fetching {detail_url}...")
    response = c.get(detail_url)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print("ERROR loading detail view")
        return
        
    print("ALL TESTS PASSED")

if __name__ == '__main__':
    test_evaluator_views()
