


from django.test import TestCase
from django.urls import reverse

from users.models import CustomUser, Role


class SuperuserHiddenTests(TestCase):
    """Superusers are managed in Django admin only; staff screens never show or edit them."""

    @classmethod
    def setUpTestData(cls):
        cls.admin_role = Role.objects.create(name='Admin')
        cls.applicant_role = Role.objects.create(name='Individual Applicant')
        cls.registrar_role = Role.objects.create(name='Registrar')
        cls.admin = CustomUser.objects.create_user(email='admin@example.com', password='x', role=cls.admin_role, is_email_verified=True)
        cls.root = CustomUser.objects.create_superuser(email='root@example.com', password='x')
        cls.root_applicant = CustomUser.objects.create_superuser(email='root2@example.com', password='x', role=cls.applicant_role)
        cls.registrar = CustomUser.objects.create_user(email='registrar@example.com', password='x', role=cls.registrar_role)

    def test_lists_hide_superusers(self):
        self.client.force_login(self.admin)
        staff = self.client.get(reverse('users:system_users_list'))
        self.assertNotContains(staff, 'root@example.com')
        self.assertContains(staff, 'registrar@example.com')
        applicants = self.client.get(reverse('users:applicant_users_list'), {'q': 'root'})
        self.assertNotContains(applicants, 'root2@example.com')
        self.assertNotContains(self.client.get(reverse('reports:users')), 'root@example.com')

    def test_superuser_pages_not_found(self):
        self.client.force_login(self.admin)
        for name in ('users:system_user_detail', 'users:system_user_update', 'users:resend_staff_activation'):
            self.assertEqual(self.client.get(reverse(name, args=[self.root.pk])).status_code, 404, name)

    def test_superuser_also_does_not_see_superusers_in_lists(self):
        self.client.force_login(self.root)
        self.assertNotContains(self.client.get(reverse('users:system_users_list')), 'root2@example.com')


class ApplicantNameDisplayTests(TestCase):
    """Applicant names, phone and region show on staff screens (they read the current profile models)."""

    def test_names_show_in_applicants_list_and_payment_page(self):
        from users.models import Applicant, Individual, Organization, ApplicantContact, ApplicantAddress
        from medicines.models import MedicineApplication, Payment
        admin = CustomUser.objects.create_user(email='a@example.com', password='x', role=Role.objects.create(name='Admin'), is_email_verified=True)
        finance = CustomUser.objects.create_user(email='f@example.com', password='x', role=Role.objects.create(name='Accountant'), is_email_verified=True)
        person = CustomUser.objects.create_user(email='p@example.com', password='x', role=Role.objects.create(name='Individual Applicant'), phone_number='0712345678')
        company = CustomUser.objects.create_user(email='c@example.com', password='x', role=Role.objects.create(name='Company Applicant'))
        p = Applicant.objects.create(user=person, applicant_type='Individual')
        Individual.objects.create(applicant=p, first_name='Asha', last_name='Juma')
        ApplicantAddress.objects.create(applicant=p, region='Tabora', district='Urambo')
        c = Applicant.objects.create(user=company, applicant_type='Organization')
        Organization.objects.create(applicant=c, organization_name='Wabeloya Natural Therapies')
        ApplicantContact.objects.create(applicant=c, mobile_phone='0755000111', email='c@example.com')

        self.client.force_login(admin)
        page = self.client.get(reverse('users:applicant_users_list'))
        self.assertContains(page, 'Asha Juma')
        self.assertContains(page, 'Wabeloya Natural Therapies')
        self.assertContains(self.client.get(reverse('users:applicant_users_list'), {'q': 'Wabeloya'}), 'c@example.com')

        app = MedicineApplication.objects.create(applicant=person, application_type='LISTING', medicine_name='Jocha', indications='x', dosage_form='UNGA', status='PENDING_APPLICATION_FEE')
        payment = Payment.objects.create(application=app, payment_type='LISTING_APP_FEE', amount=1000)
        self.client.force_login(finance)
        page = self.client.get(reverse('medicines:staff_payment_detail', args=[payment.pk]))
        self.assertContains(page, 'Asha Juma')
        self.assertContains(page, '0712345678')
        self.assertContains(page, 'Urambo, Tabora')
