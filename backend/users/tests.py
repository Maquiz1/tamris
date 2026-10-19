


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
