import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from users.models import CustomUser, Role

def test_individual():
    email = 'test_individual@example.com'
    CustomUser.objects.filter(email=email).delete()
    role, _ = Role.objects.get_or_create(name='Individual Applicant')
    user = CustomUser.objects.create_user(email=email, password='password123', role=role)
    user.is_email_verified = True
    user.save()
    c = Client()
    c.force_login(user)
    
    post_data_2 = {
        'first_name': 'John', 'last_name': 'Doe', 'sex': 'Male', 'date_of_birth': '1990-01-01', 'tin': '123456789',
        'identities-TOTAL_FORMS': '1', 'identities-INITIAL_FORMS': '0', 'identities-MIN_NUM_FORMS': '0', 'identities-MAX_NUM_FORMS': '1000',
        'identities-0-identity_type': 'NIDA (National ID)', 'identities-0-identity_number': '19900101123456789012',
        'addresses-TOTAL_FORMS': '1', 'addresses-INITIAL_FORMS': '0', 'addresses-MIN_NUM_FORMS': '0', 'addresses-MAX_NUM_FORMS': '1000',
        'addresses-0-country': 'Tanzania', 'addresses-0-region': 'Dar es Salaam', 'addresses-0-district': 'Kinondoni', 'addresses-0-ward': 'Oysterbay', 'addresses-0-street': 'Toure Drive', 'addresses-0-residency_duration': '5 Years',
        'contact-email': email, 'contact-mobile_phone': '0712345678',
        'educations-TOTAL_FORMS': '1', 'educations-INITIAL_FORMS': '0', 'educations-MIN_NUM_FORMS': '0', 'educations-MAX_NUM_FORMS': '1000',
        'educations-0-highest_level': 'Bachelor Degree', 'educations-0-institution_name': 'UDSM', 'educations-0-graduation_year': '2012', 'educations-0-registration_number': 'REG123',
    }
    c.post('/onboarding/?step=2', data=post_data_2, follow=True)
    
    df1 = SimpleUploadedFile("test1.pdf", b"file_content", content_type="application/pdf")
    df2 = SimpleUploadedFile("test2.pdf", b"file_content", content_type="application/pdf")
    c.post('/onboarding/?step=3', data={'nida_copy': df1, 'degree_certificate': df2}, follow=True)
    response = c.post('/onboarding/?step=4', data={}, follow=True)
    return response.status_code == 200

if __name__ == '__main__':
    res1 = test_individual()
    if res1:
        print("INDIVIDUAL OK")
    else:
        print("INDIVIDUAL FAIL")
