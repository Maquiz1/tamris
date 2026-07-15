from django.core.management.base import BaseCommand
from users.models import Role

class Command(BaseCommand):
    help = 'Seeds all required roles into the database'

    ROLES = [
        # ── Staff Roles ────────────────────────────────────────────
        'Admin',
        'Evaluator',
        'Inspector',
        'Accountant',

        # ── Applicant Roles ────────────────────────────────────────
        'Individual Applicant',
        'Company Applicant',
    ]

    def handle(self, *args, **kwargs):
        # Rename legacy role "Finance Officer" to "Accountant" if it exists
        try:
            finance_officer = Role.objects.get(name='Finance Officer')
            finance_officer.name = 'Accountant'
            finance_officer.save()
            self.stdout.write(self.style.SUCCESS('Successfully renamed legacy role "Finance Officer" to "Accountant" in the database.'))
        except Role.DoesNotExist:
            pass

        created_count = 0
        existing_count = 0

        for role_name in self.ROLES:
            role, created = Role.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  [CREATED]  {role_name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'  [EXISTS]   {role_name}'))
                existing_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nRole seeding completed: {created_count} created, {existing_count} already existed.'
        ))
