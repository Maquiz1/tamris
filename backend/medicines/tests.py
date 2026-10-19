import datetime
import importlib
from decimal import Decimal

from django.apps import apps as django_apps
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from medicines import services, legacy
from medicines.forms import LegacyMedicineForm, MasterMedicineApplicationForm
from medicines.models import (
    MedicineApplication, Payment, NumberSequence, InspectionSchedule, MedicineLabelAttachment, SystemSettings,
)
from medicines.views.inspections import awaiting_scheduling
from users.models import CustomUser, Role, Applicant, Individual, ApplicantIdentity, LegacyClaim

TODAY = timezone.localdate()
YY = TODAY.strftime('%y')


def pdf(name='scan.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 test', content_type='application/pdf')


class WorkflowTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_roles', verbosity=0)
        call_command('seed_fees', verbosity=0)
        SystemSettings.load()
        cls.applicant = cls.make_applicant('applicant@example.com', 'Asha', 'Juma', '19900101111110000001')
        cls.evaluator = cls.make_staff('evaluator@example.com', 'Evaluator')
        cls.finance = cls.make_staff('finance@example.com', 'Accountant')
        cls.inspector = cls.make_staff('inspector@example.com', 'Inspector')
        cls.registrar = cls.make_staff('registrar@example.com', 'Registrar')
        cls.registrar2 = cls.make_staff('registrar2@example.com', 'Registrar')
        cls.clerk = cls.make_staff('clerk@example.com', 'Data Clerk')
        cls.admin = cls.make_staff('admin@example.com', 'Admin')

    @staticmethod
    def make_staff(email, role):
        user = CustomUser.objects.create_user(email=email, password='pass12345', role=Role.objects.get(name=role), is_email_verified=True)
        return user

    @staticmethod
    def make_applicant(email, first, last, nida):
        user = CustomUser.objects.create_user(
            email=email, password='pass12345', role=Role.objects.get(name='Individual Applicant'),
            is_email_verified=True, is_onboarding_complete=True, registration_status='VERIFIED',
        )
        profile = Applicant.objects.create(user=user, applicant_type='Individual')
        Individual.objects.create(applicant=profile, first_name=first, last_name=last, sex='Female')
        ApplicantIdentity.objects.create(applicant=profile, identity_type='NIDA (National ID)', identity_number=nida, is_primary=True)
        return user

    def login(self, user):
        self.client.force_login(user)

    def new_application(self, app_type='LISTING', status='UNDER_REVIEW', **extra):
        app = MedicineApplication.objects.create(
            applicant=self.applicant, application_type=app_type, status=status,
            medicine_name=extra.pop('medicine_name', f'Dawa {MedicineApplication.all_objects.count() + 1}'),
            dosage_form='UNGA', indications='Kikohozi', medicine_color='Brown', active_ingredients='Hypoxis fischeri',
            **extra,
        )
        services.assign_reference(app)
        return app

    def pay(self, app, payment_type):
        payment = app.payments.get(payment_type=payment_type, is_verified=False)
        payment.control_number = '123456789012'
        payment.save()
        self.login(self.finance)
        response = self.client.post(reverse('medicines:staff_payment_detail', args=[payment.pk]), {'action': 'mark_paid', 'remarks': ''})
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertTrue(payment.is_verified)
        app.refresh_from_db()
        return app


class NumberingTests(WorkflowTestCase):
    def test_reference_numbers_are_per_service_and_year(self):
        a = self.new_application('LISTING')
        b = self.new_application('LISTING')
        c = self.new_application('CATEGORY_II')
        self.assertEqual(a.reference_number, f'TAHPC/LST/{TODAY.year}/0001')
        self.assertEqual(b.reference_number, f'TAHPC/LST/{TODAY.year}/0002')
        self.assertEqual(c.reference_number, f'TAHPC/REG/{TODAY.year}/0001')

    def test_certificate_numbers_use_separate_counters_and_restart_each_year(self):
        # The data migration starts this year's counters after the 200 numbers assumed used on paper
        self.assertEqual(services.next_certificate_number('LISTING', TODAY), f'TZ{YY}TL0201')
        self.assertEqual(services.next_certificate_number('LISTING', TODAY), f'TZ{YY}TL0202')
        self.assertEqual(services.next_certificate_number('CATEGORY_II', TODAY), f'TZ{YY}TM0201')
        next_year = TODAY.replace(year=TODAY.year + 1)
        self.assertEqual(services.next_certificate_number('LISTING', next_year), f'TZ{next_year:%y}TL0001')

    def test_paper_number_moves_counter_and_duplicates_are_refused(self):
        app = self.new_application('CATEGORY_II', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TM0187')
        services.register_paper_number(app.certificate_number)
        self.assertEqual(NumberSequence.objects.get(kind=NumberSequence.CERT_CATEGORY_II, year=TODAY.year).last_number, 200)
        services.register_paper_number(f'TZ{YY}TM0245')  # a paper number above the counter moves it
        self.assertEqual(NumberSequence.objects.get(kind=NumberSequence.CERT_CATEGORY_II, year=TODAY.year).last_number, 245)
        with self.assertRaises(services.WorkflowError):
            services.validate_paper_certificate_number(f'tz{YY}tm0187', 'CATEGORY_II')
        with self.assertRaises(services.WorkflowError):
            services.validate_paper_certificate_number('ABC123', 'CATEGORY_II')

    def test_one_year_validity(self):
        self.assertEqual(services.add_one_year(datetime.date(2026, 5, 20)), datetime.date(2027, 5, 20))
        self.assertEqual(services.add_one_year(datetime.date(2028, 2, 29)), datetime.date(2029, 2, 28))


class DataMigrationTests(WorkflowTestCase):
    def test_existing_numbers_are_frozen_exactly_as_printed(self):
        migration = importlib.import_module('medicines.migrations.0030_store_existing_numbers')
        full = MedicineApplication.objects.create(applicant=self.applicant, application_type='LISTING', status='FULL_REGISTRATION', medicine_name='Old Listed', indications='x', dosage_form='UNGA')
        prov = MedicineApplication.objects.create(applicant=self.applicant, application_type='CATEGORY_II', status='PENDING_REGISTRATION_FEE', medicine_name='Old Prov', indications='x', dosage_form='UNGA')
        printed_number = f"TZ{full.updated_at.strftime('%y')}TM{full.id:04d}"

        migration.forwards(django_apps, None)
        migration.forwards(django_apps, None)  # safe to run twice

        full.refresh_from_db()
        prov.refresh_from_db()
        self.assertEqual(full.certificate_number, printed_number)
        self.assertEqual(full.certificate_issued_on, timezone.localtime(full.updated_at).date())
        self.assertEqual(full.certificate_expires_on, services.add_one_year(full.certificate_issued_on))
        self.assertEqual(prov.former_reference, f'TAHPC/PROV/{prov.id:06d}')
        self.assertIsNotNone(prov.provisional_issued_on)
        self.assertTrue(full.reference_number.startswith('TAHPC/LST/'))
        seq = NumberSequence.objects.get(kind=NumberSequence.CERT_CATEGORY_II, year=TODAY.year)
        self.assertGreaterEqual(seq.last_number, max(200, full.id))


class ListingFlowTests(WorkflowTestCase):
    def test_initiate_creates_reference_and_application_fee(self):
        self.login(self.applicant)
        response = self.client.post(reverse('medicines:initiate_application', args=['LISTING']), {'medicine_name': 'Jocha'})
        self.assertEqual(response.status_code, 302)
        app = MedicineApplication.objects.get(medicine_name='Jocha')
        self.assertEqual(app.status, 'PENDING_APPLICATION_FEE')
        self.assertTrue(app.reference_number.startswith('TAHPC/LST/'))
        self.assertEqual(app.payments.filter(payment_type='LISTING_APP_FEE').count(), 1)

    def test_full_listing_flow_to_certificate(self):
        app = self.new_application('LISTING', status='PENDING_APPLICATION_FEE')
        services.create_fee(app, 'application')
        app = self.pay(app, 'LISTING_APP_FEE')
        self.assertEqual(app.status, 'DRAFT')
        self.assertTrue(any('Payment Verified' in m.subject and app.applicant.email in m.to for m in mail.outbox))

        app.status = 'PENDING_EVALUATION_FEE'
        app.save()
        services.create_fee(app, 'evaluation')
        app = self.pay(app, 'LISTING_EVAL_FEE')
        self.assertEqual(app.status, 'UNDER_REVIEW')

        self.login(self.evaluator)
        self.client.post(reverse('medicines:staff_preliminary_detail', args=[app.pk]), {'action': 'approve', 'documents_complete': 'on'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'PRELIMINARY_APPROVED')

        self.client.post(reverse('medicines:staff_scientific_detail', args=[app.pk]), {'action': 'provisional'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'PENDING_LISTING_FEE')
        self.assertEqual(app.provisional_issued_on, TODAY)
        # A second click cannot create a second listing fee
        self.client.post(reverse('medicines:staff_scientific_detail', args=[app.pk]), {'action': 'provisional'})
        self.assertEqual(app.payments.filter(payment_type='LISTING_FEE').count(), 1)

        self.login(self.applicant)
        letter = self.client.get(reverse('medicines:provisional_letter', args=[app.pk]))
        self.assertContains(letter, 'PROVISIONAL LETTER FOR LISTING OF TRADITIONAL MEDICINES')
        self.assertContains(letter, 'Asha Juma')

        app = self.pay(app, 'LISTING_FEE')
        self.assertEqual(app.status, 'PENDING_FINAL_APPROVAL')

        # Evaluators can no longer issue certificates; the Registrar does
        self.login(self.evaluator)
        self.client.post(reverse('medicines:final_approval_detail', args=[app.pk]), {'action': 'approve'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'PENDING_FINAL_APPROVAL')

        self.login(self.registrar)
        self.client.post(reverse('medicines:final_approval_detail', args=[app.pk]), {'action': 'approve'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'FULL_REGISTRATION')
        self.assertEqual(app.certificate_number, f'TZ{YY}TL0201')
        self.assertEqual(app.certificate_issued_on, TODAY)
        self.assertEqual(app.certificate_expires_on, services.add_one_year(TODAY))
        self.assertEqual(app.final_approved_by, self.registrar)

        self.login(self.applicant)
        cert = self.client.get(reverse('medicines:download_certificate', args=[app.pk]))
        self.assertContains(cert, 'LISTING OF TRADITIONAL MEDICINES', status_code=200)
        self.assertContains(cert, app.certificate_number)
        self.assertContains(cert, 'Asha Juma')
        self.assertContains(cert, 'CONDITIONS OF LISTING')
        # Provisional letter is no longer open to the applicant once the certificate exists
        response = self.client.get(reverse('medicines:provisional_letter', args=[app.pk]))
        self.assertEqual(response.status_code, 302)
        # Staff can still see it
        self.login(self.registrar)
        self.assertEqual(self.client.get(reverse('medicines:provisional_letter', args=[app.pk])).status_code, 200)

    def test_preliminary_conditions_and_resubmission(self):
        app = self.new_application('LISTING', status='UNDER_REVIEW')
        self.login(self.evaluator)
        self.client.post(reverse('medicines:staff_preliminary_detail', args=[app.pk]), {
            'action': 'conditions', 'overall_comments': 'Attach a clearer label.', 'sections_to_revise': ['DOCUMENTS'],
        })
        app.refresh_from_db()
        self.assertEqual(app.status, 'CONDITIONS_APPLIED')
        self.assertEqual(app.conditions_return_status, 'UNDER_REVIEW')
        self.assertEqual(app.evaluation.sections_to_revise, ['DOCUMENTS'])
        services.resubmit_after_conditions(app)
        app.refresh_from_db()
        self.assertEqual(app.status, 'UNDER_REVIEW')

    def test_conditions_need_comments_and_sections(self):
        app = self.new_application('LISTING', status='UNDER_REVIEW')
        self.login(self.evaluator)
        self.client.post(reverse('medicines:staff_preliminary_detail', args=[app.pk]), {'action': 'conditions'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'UNDER_REVIEW')

    def test_decisions_are_refused_in_the_wrong_status(self):
        app = self.new_application('CATEGORY_II', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TM0999')
        self.login(self.evaluator)
        self.client.post(reverse('medicines:staff_preliminary_detail', args=[app.pk]), {'action': 'approve'})
        self.client.post(reverse('medicines:staff_scientific_detail', args=[app.pk]), {'action': 'provisional'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'FULL_REGISTRATION')
        self.assertFalse(app.payments.exists())

    def test_staff_search_does_not_crash(self):
        self.new_application('LISTING', status='UNDER_REVIEW', medicine_name='Searchable')
        self.login(self.evaluator)
        response = self.client.get(reverse('medicines:staff_preliminary_list'), {'q': 'Asha', 'filter': 'all'})
        self.assertContains(response, 'Searchable')

    def test_evaluation_pages_show_uploaded_labels(self):
        app = self.new_application('LISTING', status='UNDER_REVIEW')
        MedicineLabelAttachment.objects.create(application=app, file=SimpleUploadedFile('label.png', b'x', content_type='image/png'))
        self.login(self.evaluator)
        response = self.client.get(reverse('medicines:staff_preliminary_detail', args=[app.pk]))
        self.assertContains(response, 'Sample Label 1')

    def test_upgrade_to_category_ii_works(self):
        app = self.new_application('LISTING', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TL0500',
                                   certificate_issued_on=TODAY, certificate_expires_on=services.add_one_year(TODAY))
        self.login(self.applicant)
        response = self.client.post(reverse('medicines:upgrade_to_registration', args=[app.pk]))
        self.assertEqual(response.status_code, 302)
        new_app = MedicineApplication.objects.get(application_type='CATEGORY_II', medicine_name=app.medicine_name)
        self.assertEqual(new_app.status, 'PENDING_APPLICATION_FEE')
        self.assertEqual(new_app.active_ingredients, 'Hypoxis fischeri')
        self.assertTrue(new_app.payments.filter(payment_type='CAT_II_APP_FEE').exists())


class CategoryIIFlowTests(WorkflowTestCase):
    def test_inspection_is_scheduled_once_fee_paid_and_reinspection_is_free(self):
        app = self.new_application('CATEGORY_II', status='UNDER_REVIEW')
        self.login(self.evaluator)
        self.client.post(reverse('medicines:staff_preliminary_detail', args=[app.pk]), {'action': 'approve'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'PENDING_INSPECTION_FEE')
        app = self.pay(app, 'CAT_II_INSPECTION_FEE')
        self.assertEqual(app.status, 'READY_FOR_INSPECTION')
        self.assertIn(app, awaiting_scheduling())

        start = timezone.now() + datetime.timedelta(days=3)
        schedule_data = {
            'assigned_inspectors': [self.inspector.pk],
            'start_date_time': start.strftime('%Y-%m-%dT%H:%M'),
            'end_date_time': (start + datetime.timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M'),
            'check_manufacturing_area': 'on', 'check_cleanliness': 'on',
        }
        self.login(self.evaluator)
        self.client.post(reverse('medicines:schedule_inspection', args=[app.pk]), schedule_data)
        schedule = InspectionSchedule.objects.get(application=app)
        self.assertEqual(app.payments.filter(payment_type='CAT_II_INSPECTION_FEE').count(), 1)
        self.assertNotIn(app, awaiting_scheduling())

        self.login(self.inspector)
        self.client.post(reverse('medicines:submit_inspection_report', args=[schedule.pk]), {
            'manufacturing_area_remarks': 'Small', 'cleanliness_remarks': 'Poor', 'remarks': 'Not compliant', 'gmp_compliant': '',
        })
        app.refresh_from_db()
        self.assertEqual(app.status, 'INSPECTION_COMPLETED')

        # Not compliant: conditions with re-inspection
        self.login(self.evaluator)
        self.client.post(reverse('medicines:staff_scientific_detail', args=[app.pk]), {
            'action': 'conditions', 'overall_comments': 'Clean the site.', 'requires_reinspection': '1',
        })
        app.refresh_from_db()
        self.assertEqual(app.status, 'CONDITIONS_APPLIED')
        services.resubmit_after_conditions(app)
        app.refresh_from_db()
        self.assertEqual(app.status, 'READY_FOR_INSPECTION')
        self.assertIn(app, awaiting_scheduling())
        self.assertEqual(app.payments.filter(payment_type='CAT_II_INSPECTION_FEE').count(), 1)

    def test_old_order_applications_still_get_scheduled(self):
        app = self.new_application('CATEGORY_II', status='PRELIMINARY_APPROVED')
        self.assertIn(app, awaiting_scheduling())
        start = timezone.now() + datetime.timedelta(days=1)
        self.login(self.evaluator)
        self.client.post(reverse('medicines:schedule_inspection', args=[app.pk]), {
            'assigned_inspectors': [self.inspector.pk],
            'start_date_time': start.strftime('%Y-%m-%dT%H:%M'),
            'end_date_time': (start + datetime.timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
        })
        app.refresh_from_db()
        self.assertEqual(app.status, 'PENDING_INSPECTION_FEE')
        self.assertEqual(app.payments.filter(payment_type='CAT_II_INSPECTION_FEE').count(), 1)

    def test_registration_certificate_and_letter_render(self):
        app = self.new_application('CATEGORY_II', status='PENDING_REGISTRATION_FEE', provisional_issued_on=TODAY,
                                   shelf_life=2, shelf_life_duration_type='YEARS', net_weight_volume=Decimal('70.00'),
                                   net_weight_volume_unit='g', packaging_color='White', lid_color='white')
        self.login(self.applicant)
        self.assertContains(self.client.get(reverse('medicines:provisional_letter', args=[app.pk])),
                            'PROVISIONAL LETTER FOR REGISTRATION OF CATEGORY II TRADITIONAL MEDICINES')
        services.create_fee(app, 'final')
        app = self.pay(app, 'CAT_II_REGISTRATION_FEE')
        services.issue_certificate(app, self.registrar)
        app.refresh_from_db()
        self.login(self.applicant)
        cert = self.client.get(reverse('medicines:download_certificate', args=[app.pk]))
        self.assertContains(cert, 'REGISTRATION OF CATEGORY II TRADITIONAL MEDICINES')
        self.assertContains(cert, 'CONDITIONS OF REGISTRATION')
        self.assertContains(cert, '>24<')  # 2 years shown in months
        self.assertTrue(app.certificate_number.startswith(f'TZ{YY}TM'))


class PaymentTests(WorkflowTestCase):
    def test_reject_clears_submission_and_verified_cannot_be_reversed(self):
        app = self.new_application('LISTING', status='PENDING_APPLICATION_FEE')
        payment = services.create_fee(app, 'application')
        payment.control_number = '123456789012'
        payment.save()
        self.login(self.finance)
        self.client.post(reverse('medicines:staff_payment_detail', args=[payment.pk]), {'action': 'mark_unpaid', 'remarks': 'Not received'})
        payment.refresh_from_db()
        self.assertIsNone(payment.control_number)
        self.assertTrue(app.requires_applicant_action)

        payment.control_number = '123456789012'
        payment.save()
        services.verify_payment(payment, self.finance)
        with self.assertRaises(services.WorkflowError):
            services.reject_payment(payment, self.finance, 'oops')

    def test_evaluators_cannot_verify_payments(self):
        app = self.new_application('LISTING', status='PENDING_APPLICATION_FEE')
        payment = services.create_fee(app, 'application')
        payment.control_number = '123456789012'
        payment.save()
        self.login(self.evaluator)
        self.client.post(reverse('medicines:staff_payment_detail', args=[payment.pk]), {'action': 'mark_paid'})
        payment.refresh_from_db()
        self.assertFalse(payment.is_verified)


class RenewalTests(WorkflowTestCase):
    def test_renewal_extends_one_year_and_keeps_number(self):
        expires = TODAY + datetime.timedelta(days=30)
        app = self.new_application('LISTING', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TL0300',
                                   certificate_issued_on=expires.replace(year=expires.year - 1), certificate_expires_on=expires)
        self.assertTrue(app.can_renew)
        self.login(self.applicant)
        self.client.post(reverse('medicines:start_renewal', args=[app.pk]))
        self.assertEqual(app.payments.filter(payment_type='LISTING_RENEWAL_FEE').count(), 1)
        self.assertFalse(app.can_renew)  # already started
        app = self.pay(app, 'LISTING_RENEWAL_FEE')
        self.assertEqual(app.certificate_expires_on, services.add_one_year(expires))
        self.assertEqual(app.certificate_number, f'TZ{YY}TL0300')
        self.assertEqual(app.renewal_count, 1)

    def test_renewal_not_open_early(self):
        app = self.new_application('LISTING', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TL0301',
                                   certificate_issued_on=TODAY, certificate_expires_on=services.add_one_year(TODAY))
        self.assertFalse(app.can_renew)

    def test_reminders_sent_once(self):
        app = self.new_application('LISTING', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TL0302',
                                   certificate_issued_on=TODAY, certificate_expires_on=TODAY + datetime.timedelta(days=25))
        call_command('send_renewal_reminders', verbosity=0)
        call_command('send_renewal_reminders', verbosity=0)
        app.refresh_from_db()
        self.assertEqual(sorted(app.renewal_reminders_sent), [30, 90])
        self.assertEqual(len([m for m in mail.outbox if app.certificate_number in m.subject]), 1)


class LegacyTests(WorkflowTestCase):
    def legacy_applicant(self, email='paper@example.com', nida='19800101111110000099'):
        return legacy.create_legacy_applicant({
            'applicant_type': 'Individual', 'email': email, 'first_name': 'Joseph', 'last_name': 'Kajigili',
            'identity_type': 'NIDA (National ID)', 'identity_number': nida, 'tin': None,
        }, {}, self.clerk)

    def legacy_form(self, applicant, **overrides):
        data = {
            'applicant': applicant.pk, 'application_type': 'CATEGORY_II', 'outcome': 'CERTIFIED',
            'medicine_name': 'Jocha', 'dosage_form': 'UNGA', 'storage_conditions': 'JOTO_LA_KAWAIDA',
            'certificate_number': f'TZ{YY}TM0187', 'certificate_issued_on': '2026-05-20', 'certificate_expires_on': '2027-06-30',
            'pay-TOTAL_FORMS': '3', 'pay-INITIAL_FORMS': '0', 'pay-MIN_NUM_FORMS': '0', 'pay-MAX_NUM_FORMS': '6',
            'pay-0-payment_type': 'CAT_II_REGISTRATION_FEE', 'pay-0-amount': '',
        }
        data.update(overrides)
        return data

    def test_legacy_certificate_waits_for_another_registrar(self):
        owner = self.legacy_applicant()
        self.assertFalse(owner.has_usable_password())
        self.assertEqual(owner.registration_status, 'VERIFIED')

        self.login(self.clerk)
        response = self.client.post(reverse('medicines:legacy_medicine_create'), {**self.legacy_form(owner), 'legacy_certificate_scan': pdf()})
        self.assertEqual(response.status_code, 302, getattr(response, 'context', {}) and response.context['form'].errors)
        app = MedicineApplication.objects.get(medicine_name='Jocha')
        self.assertEqual(app.legacy_verification_status, 'PENDING')
        self.assertEqual(app.certificate_expires_on, datetime.date(2027, 6, 30))  # kept exactly as printed
        self.assertGreaterEqual(NumberSequence.objects.get(kind=NumberSequence.CERT_CATEGORY_II, year=2000 + int(YY)).last_number, 187)
        payment = app.payments.get()
        self.assertTrue(payment.paid_before_system)
        self.assertIsNone(payment.amount_paid)
        self.assertFalse(app.is_visible_to_applicant)
        self.assertEqual(len([m for m in mail.outbox if owner.email in m.to]), 0)

        # The clerk who also holds the Registrar role still cannot verify their own entry
        self.clerk.additional_roles.add(Role.objects.get(name='Registrar'))
        with self.assertRaises(services.WorkflowError):
            legacy.verify_legacy_certificate(app, self.clerk)

        self.login(self.registrar)
        self.client.post(reverse('medicines:legacy_verification_detail', args=[app.pk]), {'action': 'verify'})
        app.refresh_from_db()
        owner.refresh_from_db()
        self.assertEqual(app.legacy_verification_status, 'VERIFIED')
        self.assertTrue(app.is_visible_to_applicant)
        self.assertIsNotNone(owner.legacy_invited_at)
        self.assertTrue(any(owner.email in m.to and 'password' in m.body for m in mail.outbox))

    def test_duplicate_paper_number_is_refused(self):
        owner = self.legacy_applicant()
        self.new_application('CATEGORY_II', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TM0187')
        form = LegacyMedicineForm(self.legacy_form(owner), {'legacy_certificate_scan': pdf()})
        self.assertFalse(form.is_valid())
        self.assertIn('certificate_number', form.errors)

    def test_rejected_paper_application_saved_for_history(self):
        owner = self.legacy_applicant()
        form = LegacyMedicineForm(self.legacy_form(owner, outcome='REJECTED', rejection_reason='Unsafe', medicine_name='Old Rejected'))
        self.assertTrue(form.is_valid(), form.errors)
        app = legacy.save_legacy_medicine(form, None, self.clerk)
        self.assertEqual(app.status, 'REJECTED')
        self.assertIsNone(app.certificate_number)

    def test_returned_record_can_be_corrected(self):
        owner = self.legacy_applicant()
        form = LegacyMedicineForm(self.legacy_form(owner), {'legacy_certificate_scan': pdf()})
        self.assertTrue(form.is_valid(), form.errors)
        app = legacy.save_legacy_medicine(form, None, self.clerk)
        legacy.return_legacy_record(app, self.registrar, 'Expiry date is wrong')
        app.refresh_from_db()
        self.assertEqual(app.legacy_verification_status, 'RETURNED')
        form = LegacyMedicineForm(self.legacy_form(owner, certificate_expires_on='2027-05-20'), instance=app)
        self.assertTrue(form.is_valid(), form.errors)
        app = legacy.save_legacy_medicine(form, None, self.clerk)
        self.assertEqual(app.legacy_verification_status, 'PENDING')
        self.assertEqual(app.certificate_expires_on, datetime.date(2027, 5, 20))

    def test_legacy_scan_shown_until_first_renewal(self):
        owner = self.legacy_applicant()
        form = LegacyMedicineForm(self.legacy_form(owner), {'legacy_certificate_scan': pdf()})
        self.assertTrue(form.is_valid(), form.errors)
        app = legacy.save_legacy_medicine(form, None, self.clerk)
        legacy.verify_legacy_certificate(app, self.registrar)
        self.assertTrue(app.shows_original_scan)
        self.client.force_login(owner)
        response = self.client.get(reverse('medicines:download_certificate', args=[app.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(app.legacy_certificate_scan.url, response['Location'])

    def test_claim_links_paper_records_to_new_account(self):
        owner = self.legacy_applicant(nida='19700101111110000077')
        form = LegacyMedicineForm(self.legacy_form(owner), {'legacy_certificate_scan': pdf()})
        self.assertTrue(form.is_valid(), form.errors)
        app = legacy.save_legacy_medicine(form, None, self.clerk)

        newcomer = self.make_applicant('new@example.com', 'Joseph', 'Kajigili', '19700101111110000077')
        self.assertEqual(legacy.find_legacy_matches(newcomer), [owner])
        self.login(newcomer)
        self.client.post(reverse('medicines:legacy_claim_request', args=[owner.pk]))
        claim = LegacyClaim.objects.get(new_user=newcomer)
        self.assertIn('19700101111110000077', claim.matched_on)

        self.login(self.registrar)
        self.client.post(reverse('medicines:claim_list'), {'claim_id': claim.pk, 'action': 'confirm'})
        app.refresh_from_db()
        owner.refresh_from_db()
        self.assertEqual(app.applicant, newcomer)
        self.assertFalse(owner.is_active)
        self.assertEqual(legacy.find_legacy_matches(newcomer), [])


class MandatoryDocumentTests(WorkflowTestCase):
    def test_listing_requires_label_and_ingredients_document(self):
        app = self.new_application('LISTING', status='DRAFT')
        form = MasterMedicineApplicationForm({}, {}, instance=app)
        self.assertFalse(form.is_valid())
        self.assertIn('sample_label', form.errors)
        self.assertIn('ingredients_info_doc', form.errors)
        self.assertNotIn('statement_of_efficacy', form.errors)

    def test_settings_change_mandatory_list(self):
        settings_obj = SystemSettings.load()
        settings_obj.mandatory_listing_documents = ['statement_of_efficacy']
        settings_obj.save()
        app = self.new_application('LISTING', status='DRAFT')
        form = MasterMedicineApplicationForm({}, {}, instance=app)
        form.is_valid()
        self.assertIn('statement_of_efficacy', form.errors)
        self.assertNotIn('sample_label', form.errors)


class RolePageTests(WorkflowTestCase):
    def test_role_dashboards_and_pages_load(self):
        pages = [
            (self.registrar, 'medicines:registrar_dashboard'),
            (self.registrar, 'medicines:final_approval_list'),
            (self.registrar, 'medicines:legacy_verification_list'),
            (self.registrar, 'medicines:claim_list'),
            (self.clerk, 'medicines:legacy_dashboard'),
            (self.clerk, 'medicines:legacy_applicant_create'),
            (self.clerk, 'medicines:legacy_medicine_create'),
            (self.admin, 'medicines:system_settings'),
            (self.applicant, 'medicines:applicant_certificate_list'),
            (self.applicant, 'users:dashboard'),
            (self.evaluator, 'medicines:inspection_dashboard'),
            (self.finance, 'medicines:staff_payment_list'),
        ]
        for user, name in pages:
            self.login(user)
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, f'{name} as {user.email}')

    def test_dashboard_sends_new_roles_to_their_work(self):
        committee = self.make_staff('committee@example.com', 'Committee')
        for user, target in ((self.registrar, 'medicines:registrar_dashboard'), (self.clerk, 'medicines:legacy_dashboard'), (committee, 'reports:dashboard')):
            self.login(user)
            self.assertRedirects(self.client.get(reverse('users:dashboard')), reverse(target), fetch_redirect_response=False)

    def test_data_clerk_cannot_approve(self):
        app = self.new_application('LISTING', status='PENDING_FINAL_APPROVAL')
        self.login(self.clerk)
        self.client.post(reverse('medicines:final_approval_detail', args=[app.pk]), {'action': 'approve'})
        app.refresh_from_db()
        self.assertEqual(app.status, 'PENDING_FINAL_APPROVAL')

    def test_counter_cannot_go_below_issued_number(self):
        self.new_application('CATEGORY_II', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TM0250')
        self.login(self.admin)
        self.client.post(reverse('medicines:system_settings'), {'form': 'counters', 'listing_last_number': 10, 'category_ii_last_number': 100})
        seq = NumberSequence.objects.get(kind=NumberSequence.CERT_CATEGORY_II, year=TODAY.year)
        self.assertNotEqual(seq.last_number, 100)
        self.assertEqual(NumberSequence.objects.get(kind=NumberSequence.CERT_LISTING, year=TODAY.year).last_number, 10)


class PageSmokeTests(WorkflowTestCase):
    def test_pages_render_with_data(self):
        listed = self.new_application('LISTING', status='FULL_REGISTRATION', certificate_number=f'TZ{YY}TL0400',
                                      certificate_issued_on=TODAY, certificate_expires_on=TODAY + datetime.timedelta(days=20))
        provisional = self.new_application('CATEGORY_II', status='PENDING_REGISTRATION_FEE', provisional_issued_on=TODAY)
        services.create_fee(provisional, 'final')
        final = self.new_application('CATEGORY_II', status='PENDING_FINAL_APPROVAL')
        cond = self.new_application('LISTING', status='CONDITIONS_APPLIED', conditions_return_status='UNDER_REVIEW')
        payment = provisional.payments.get()
        checks = [
            (self.applicant, reverse('medicines:applicant_applications') + '?filter=apps_all'),
            (self.applicant, reverse('medicines:applicant_applications') + '?filter=tasks_all'),
            (self.applicant, reverse('medicines:applicant_payment_list')),
            (self.applicant, reverse('medicines:applicant_listed_medicines')),
            (self.applicant, reverse('medicines:applicant_registered_medicines')),
            (self.applicant, reverse('medicines:applicant_application_detail', args=[listed.pk])),
            (self.applicant, reverse('medicines:applicant_certificate_list')),
            (self.applicant, reverse('medicines:applicant_reports')),
            (self.applicant, reverse('medicines:edit_application', args=[cond.pk])),
            (self.applicant, reverse('medicines:submit_payment', args=[payment.pk])),
            (self.applicant, reverse('users:dashboard')),
            (self.evaluator, reverse('medicines:staff_preliminary_list') + '?filter=all'),
            (self.evaluator, reverse('medicines:staff_scientific_list') + '?filter=all'),
            (self.evaluator, reverse('medicines:staff_scientific_detail', args=[final.pk])),
            (self.evaluator, reverse('users:dashboard')),
            (self.registrar, reverse('medicines:final_approval_detail', args=[final.pk])),
            (self.registrar, reverse('medicines:final_approval_list') + '?show=decided'),
            (self.registrar, reverse('medicines:staff_scientific_detail', args=[final.pk])),
            (self.finance, reverse('medicines:staff_payment_detail', args=[payment.pk])),
            (self.finance, reverse('users:dashboard')),
            (self.admin, reverse('reports:medicines')),
            (self.admin, reverse('reports:applications')),
            (self.admin, reverse('reports:payments')),
            (self.admin, reverse('reports:dashboard')),
            (self.admin, reverse('users:dashboard')),
        ]
        for user, url in checks:
            self.login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f'{url} as {user.email}')
        self.login(self.applicant)
        self.assertContains(self.client.get(reverse('medicines:applicant_certificate_list')), 'Renew')


class OnboardingDocumentTests(WorkflowTestCase):
    def test_company_needs_brela_tin_and_licence(self):
        from users.forms import CompanyDocumentForm, PractitionerDocumentForm
        from users.models import Organization
        user = CustomUser.objects.create_user(email='co@example.com', password='x', role=Role.objects.get(name='Company Applicant'), is_email_verified=True)
        profile = Applicant.objects.create(user=user, applicant_type='Organization')
        Organization.objects.create(applicant=profile, organization_name='Wabeloya', tin='123456789')
        form = CompanyDocumentForm({}, {'brela_certificate': pdf('b.pdf')}, instance=profile)
        self.assertFalse(form.is_valid())
        self.assertIn('TIN certificate', str(form.errors))
        form = CompanyDocumentForm({}, {'brela_certificate': pdf('b.pdf'), 'tin_certificate': pdf('t.pdf'), 'business_license': pdf('l.pdf')}, instance=profile)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(profile.is_profile_complete)
        # Individuals only need their NIDA or passport number by default
        self.assertTrue(self.applicant.applicant_profile.is_profile_complete)
        self.assertTrue(PractitionerDocumentForm({}, {}, instance=self.applicant.applicant_profile).is_valid())

    def test_onboarding_documents_step_loads(self):
        user = CustomUser.objects.create_user(email='new2@example.com', password='x', role=Role.objects.get(name='Individual Applicant'), is_email_verified=True)
        profile = Applicant.objects.create(user=user, applicant_type='Individual')
        Individual.objects.create(applicant=profile, first_name='A', last_name='B', sex='Male')
        self.login(user)
        self.assertEqual(self.client.get(reverse('users:onboarding') + '?step=2').status_code, 200)
