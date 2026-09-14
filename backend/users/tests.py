from django.test import TestCase
from users.models import CustomUser, Role, UserProfile, CompanyProfile
from users.forms import CustomUserCreationForm, PractitionerDetailForm, CompanyDetailForm

class OnboardingFormsTestCase(TestCase):
    def setUp(self):
        self.ind_role = Role.objects.create(name='Individual Applicant')
        self.comp_role = Role.objects.create(name='Company Applicant')
        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            password='password123',
            role=self.ind_role
        )

    def test_registration_form_has_no_phone_number(self):
        form = CustomUserCreationForm()
        self.assertNotIn('phone_number', form.fields)
        self.assertIn('email', form.fields)

    def test_practitioner_detail_form_saves_profile_and_phone(self):
        form_data = {
            'full_name': 'John Doe',
            'sex': 'Male',
            'age': 34,
            'date_of_birth': '1990-01-01',
            'nida_number': '19900101-12345-67890-12',
            'tin': '123456789',
            'country': 'Tanzania',
            'region': 'Dar es Salaam',
            'district': 'Kinondoni',
            'address': '123 Main St',
            'phone_number': '0712345678'
        }
        form = PractitionerDetailForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        profile = form.save()
        
        self.assertEqual(profile.full_name, 'John Doe')
        self.assertEqual(profile.sex, 'Male')
        self.assertEqual(profile.age, 34)
        self.assertEqual(str(profile.date_of_birth), '1990-01-01')
        self.assertEqual(profile.country, 'Tanzania')
        self.assertEqual(profile.region, 'Dar es Salaam')
        self.assertEqual(profile.district, 'Kinondoni')
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '0712345678')

    def test_company_detail_form_saves_profile_and_phone(self):
        self.user.role = self.comp_role
        self.user.save()
        
        form_data = {
            'company_name': 'Test Pharma Ltd',
            'brela_number': 'BRELA12345',
            'tin': '987654321',
            'country': 'Tanzania',
            'region': 'Arusha',
            'district': 'Arusha Urban',
            'physical_address': 'Plot 45 Industrial Area',
            'phone_number': '0787654321'
        }
        form = CompanyDetailForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        profile = form.save()

        self.assertEqual(profile.company_name, 'Test Pharma Ltd')
        self.assertEqual(profile.brela_number, 'BRELA12345')
        self.assertEqual(profile.country, 'Tanzania')
        self.assertEqual(profile.region, 'Arusha')
        self.assertEqual(profile.district, 'Arusha Urban')
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '0787654321')

    def test_applicant_dashboard_shows_complete_profile_notice(self):
        self.user.is_email_verified = True
        self.user.is_onboarding_complete = False
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Complete Your Profile Before Any Application')
    def test_onboarding_save_draft_and_continue(self):
        self.user.is_email_verified = True
        self.user.save()
        self.client.force_login(self.user)

        # Test Save Draft with partial data
        draft_data = {
            'first_name': 'Jane',
            'save_draft': '1'
        }
        response = self.client.post('/onboarding/', draft_data)
        self.assertEqual(response.status_code, 302)
        
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.first_name, 'Jane')

        # Test Save & Continue with complete data
        continue_data = {
            'full_name': 'Jane Doe',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'sex': 'Female',
            'age': 28,
            'date_of_birth': '1995-01-01',
            'nida_number': '19950101-12345-67890-12',
            'tin': '123456789',
            'country': 'Tanzania',
            'phone_number': '0711223344'
        }
        response = self.client.post('/onboarding/', continue_data)
        self.assertEqual(response.status_code, 302)
        
        profile.refresh_from_db()
        self.assertEqual(profile.last_name, 'Doe')
        self.assertEqual(profile.sex, 'Female')
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '0711223344')

    def test_top_step_wizard_clickable_navigation(self):
        self.user.is_email_verified = True
        self.user.save()
        self.client.force_login(self.user)

        response = self.client.get('/onboarding/?step=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['step'], 1)
        self.assertContains(response, 'href="/onboarding/?step=1"')
