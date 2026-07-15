from django.core.management.base import BaseCommand
from users.models import Role

class Command(BaseCommand):
    help = 'Seeds all required roles into the database'

    ROLES = [
        # ── Staff Roles ────────────────────────────────────────────
        'Admin',
        'Evaluator',
        'Inspector',
        'Finance Officer',

        # ── Applicant Roles ────────────────────────────────────────
        'Individual Applicant',
        'Company Applicant',
    ]

    def handle(self, *args, **kwargs):
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

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done! {created_count} role(s) created, {existing_count} already existed.'
        ))
