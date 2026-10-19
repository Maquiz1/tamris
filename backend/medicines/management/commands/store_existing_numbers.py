import importlib

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Store certificate numbers, provisional references and application references for records '
        'that do not have them yet, exactly as the old code printed them. Safe to run more than once.'
    )

    def handle(self, *args, **options):
        migration = importlib.import_module('medicines.migrations.0030_store_existing_numbers')
        migration.forwards(apps, None)
        self.stdout.write(self.style.SUCCESS('Existing numbers stored.'))
