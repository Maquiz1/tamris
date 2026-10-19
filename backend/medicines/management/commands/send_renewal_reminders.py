from django.core.management.base import BaseCommand
from django.utils import timezone

from medicines.models import MedicineApplication
from users.emails import notify_renewal_reminder, notify_certificate_expired

REMINDER_DAYS = [90, 30, 7]


class Command(BaseCommand):
    help = 'Email applicants whose certificates expire in 90, 30 or 7 days, and those that have expired. Run once a day.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent = 0
        certificates = MedicineApplication.objects.filter(
            status='FULL_REGISTRATION', is_void=False, certificate_expires_on__isnull=False,
        ).exclude(is_legacy=True, legacy_verification_status__in=['PENDING', 'RETURNED'])

        for app in certificates:
            done = list(app.renewal_reminders_sent or [])
            days_left = (app.certificate_expires_on - today).days
            if app.pending_renewal_payment and app.pending_renewal_payment.control_number:
                continue  # renewal already paid, waiting for Finance
            if days_left < 0:
                if 'expired' not in done:
                    notify_certificate_expired(app)
                    done.append('expired')
            else:
                due = [d for d in REMINDER_DAYS if days_left <= d and d not in done]
                if due:
                    notify_renewal_reminder(app, days_left)
                    done.extend(due)  # one email even if several reminders were missed
            if done != list(app.renewal_reminders_sent or []):
                app.renewal_reminders_sent = done
                app.save(update_fields=['renewal_reminders_sent'])
                sent += 1
        self.stdout.write(self.style.SUCCESS(f'Renewal reminders sent: {sent}'))
