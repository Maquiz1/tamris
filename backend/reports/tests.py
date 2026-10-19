import datetime
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from medicines.models import MedicineApplication, Payment, InspectionSchedule
from users.models import CustomUser, Role

TODAY = timezone.localdate()


class ReportTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_roles', verbosity=0)
        role = lambda n: Role.objects.get(name=n)
        cls.admin = CustomUser.objects.create_user(email='admin@x.com', password='x', role=role('Admin'), is_email_verified=True)
        cls.finance = CustomUser.objects.create_user(email='fin@x.com', password='x', role=role('Accountant'), is_email_verified=True)
        cls.clerk = CustomUser.objects.create_user(email='clerk@x.com', password='x', role=role('Data Clerk'), is_email_verified=True)
        cls.committee = CustomUser.objects.create_user(email='com@x.com', password='x', role=role('Committee'), is_email_verified=True)
        cls.applicant = CustomUser.objects.create_user(email='app@x.com', password='x', role=role('Individual Applicant'))

    def app(self, **kw):
        defaults = dict(applicant=self.applicant, application_type='LISTING', status='UNDER_REVIEW',
                        medicine_name=f'Dawa {MedicineApplication.all_objects.count()}', indications='x', dosage_form='UNGA')
        defaults.update(kw)
        return MedicineApplication.objects.create(**defaults)

    def pay(self, app, **kw):
        defaults = dict(application=app, payment_type='LISTING_APP_FEE', amount=Decimal('10000'))
        defaults.update(kw)
        return Payment.objects.create(**defaults)


class AccessTests(ReportTestCase):
    def test_roles_only_open_their_reports(self):
        self.client.force_login(self.clerk)
        self.assertEqual(self.client.get(reverse('reports:payments')).status_code, 302)
        self.assertEqual(self.client.get(reverse('reports:revenue')).status_code, 302)
        self.assertEqual(self.client.get(reverse('reports:medicines')).status_code, 200)
        self.client.force_login(self.finance)
        self.assertEqual(self.client.get(reverse('reports:payments')).status_code, 200)
        self.assertEqual(self.client.get(reverse('reports:applications')).status_code, 302)
        self.client.force_login(self.applicant)
        self.assertEqual(self.client.get(reverse('reports:dashboard')).status_code, 302)

    def test_every_report_and_export_loads_for_committee(self):
        self.client.force_login(self.committee)
        for name in ('dashboard', 'applications', 'payments', 'revenue', 'renewals', 'medicines', 'evaluations', 'inspections', 'users'):
            self.assertEqual(self.client.get(reverse(f'reports:{name}')).status_code, 200, name)
            if name != 'dashboard':
                response = self.client.get(reverse(f'reports:{name}'), {'export': 'csv'})
                self.assertEqual(response['Content-Type'], 'text/csv', name)

    def test_dashboard_hides_cards_the_user_cannot_open(self):
        self.client.force_login(self.clerk)
        page = self.client.get(reverse('reports:dashboard'))
        self.assertNotContains(page, reverse('reports:payments'))
        self.assertContains(page, reverse('reports:medicines'))


class PaymentReportTests(ReportTestCase):
    def test_status_uses_control_number_and_totals_follow_filters(self):
        a = self.app()
        self.pay(a)  # awaiting
        self.pay(a, control_number='123456789012')  # submitted, no receipt yet
        self.pay(a, control_number='123456789013', is_verified=True, amount_paid=Decimal('9000'), verified_at=timezone.now())
        old = self.pay(a, control_number='123456789014', is_verified=True, verified_at=timezone.now())
        Payment.objects.filter(pk=old.pk).update(created_at=timezone.now() - datetime.timedelta(days=400))
        self.pay(a, paid_before_system=True, is_verified=True, amount_paid=Decimal('5000'))
        self.client.force_login(self.finance)

        page = self.client.get(reverse('reports:payments'))
        self.assertEqual(page.context['awaiting_count'], 1)
        self.assertEqual(page.context['pending_count'], 1)
        self.assertEqual(page.context['total_verified_amount'], Decimal('19000'))  # 9000 paid + 10000 billed (no amount entered)
        self.assertEqual(page.context['total_legacy_amount'], Decimal('5000'))

        since = (TODAY - datetime.timedelta(days=30)).isoformat()
        page = self.client.get(reverse('reports:payments'), {'start_date': since, 'source': 'system'})
        self.assertEqual(page.context['total_verified_amount'], Decimal('9000'))
        self.assertEqual(page.context['total_legacy_amount'], 0)
        self.assertContains(page, f'value="{since}"')

    def test_revenue_by_month_counts_received_money_by_verification_date(self):
        a = self.app()
        self.pay(a, control_number='123456789012', is_verified=True, amount_paid=Decimal('7000'), verified_at=timezone.now())
        self.pay(a, payment_type='LISTING_FEE', amount=Decimal('20000'), control_number='123456789013', is_verified=True, verified_at=timezone.now())
        self.pay(a, paid_before_system=True, is_verified=True, amount_paid=Decimal('3000'), verified_at=timezone.now())
        self.pay(a, control_number='123456789014')  # not verified: not revenue
        self.client.force_login(self.finance)
        page = self.client.get(reverse('reports:revenue'))
        self.assertEqual(page.context['grand_total'], Decimal('27000'))
        self.assertEqual(page.context['legacy_total'], Decimal('3000'))
        self.assertEqual(len(page.context['month_labels']), 12)
        self.assertEqual(page.context['month_totals'][-1], Decimal('27000'))


class RegisterAndRenewalTests(ReportTestCase):
    def test_renewal_windows(self):
        cert = lambda days, **kw: self.app(status='FULL_REGISTRATION', certificate_number=f'TZ26TL{9000 + days + 500:04d}',
                                          certificate_issued_on=TODAY - datetime.timedelta(days=300),
                                          certificate_expires_on=TODAY + datetime.timedelta(days=days), **kw)
        cert(-5)
        cert(5)
        cert(25)
        cert(80)
        cert(200)
        cert(10, is_legacy=True, legacy_verification_status='PENDING')  # not verified yet: left out
        self.client.force_login(self.committee)
        page = self.client.get(reverse('reports:renewals'))
        self.assertEqual(page.context['counts'], {'expired': 1, '7': 1, '30': 2, '90': 3})
        self.assertEqual(page.context['certificates'].paginator.count, 3)
        self.assertEqual(self.client.get(reverse('reports:renewals'), {'window': 'expired'}).context['certificates'].paginator.count, 1)

        register = self.client.get(reverse('reports:medicines'))
        self.assertEqual(register.context['full_count'], 4)
        self.assertEqual(register.context['provisional_count'], 1)

    def test_void_and_unverified_legacy_left_out_and_labels_readable(self):
        self.app(status='PENDING_EVALUATION_FEE')
        self.app(is_void=True)
        self.app(status='FULL_REGISTRATION', is_legacy=True, legacy_verification_status='PENDING', certificate_number='TZ26TM0001')
        self.client.force_login(self.admin)
        page = self.client.get(reverse('reports:applications'))
        self.assertEqual(page.context['total_count'], 1)
        dashboard = self.client.get(reverse('reports:dashboard'))
        self.assertIn('Pending: Ada ya tathmini', dashboard.context['status_labels'])
        self.assertNotIn('PENDING_EVALUATION_FEE', dashboard.context['status_labels'])

    def test_lists_are_paged(self):
        for _ in range(30):
            self.app()
        self.client.force_login(self.admin)
        page = self.client.get(reverse('reports:applications'), {'type': 'LISTING'})
        self.assertEqual(len(page.context['applications'].object_list), 25)
        self.assertContains(page, 'type=LISTING&page=2')


class InspectionReportTests(ReportTestCase):
    def test_outcomes_counted(self):
        a = self.app(application_type='CATEGORY_II', status='INSPECTION_COMPLETED')
        b = self.app(application_type='CATEGORY_II', status='INSPECTION_COMPLETED')
        start = timezone.now()
        InspectionSchedule.objects.create(application=a, status='COMPLETED', gmp_compliant=False, start_date_time=start)
        InspectionSchedule.objects.create(application=a, status='COMPLETED', gmp_compliant=True, start_date_time=start)
        InspectionSchedule.objects.create(application=b, status='COMPLETED', gmp_compliant=True, start_date_time=start)
        InspectionSchedule.objects.create(application=b, status='SCHEDULED', start_date_time=start)
        self.client.force_login(self.committee)
        page = self.client.get(reverse('reports:inspections'))
        self.assertEqual(page.context['compliant_count'], 2)
        self.assertEqual(page.context['not_compliant_count'], 1)
        self.assertEqual(page.context['reinspection_count'], 1)
        self.assertEqual(self.client.get(reverse('reports:inspections'), {'result': 'not_compliant'}).context['inspections'].paginator.count, 1)
