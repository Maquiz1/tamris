from django.core.management.base import BaseCommand
from medicines.models import FeeConfiguration
from core.utils.fees import FEE_TYPES, DEFAULT_AMOUNTS

class Command(BaseCommand):
    help = 'Seeds initial fee configurations with default amounts.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding fee configurations...')
        
        created_count = 0
        updated_count = 0
        
        for fee_code, description in FEE_TYPES:
            default_amount = DEFAULT_AMOUNTS.get(fee_code, 0.00)
            
            obj, created = FeeConfiguration.objects.update_or_create(
                fee_type=fee_code,
                defaults={'amount': default_amount, 'is_active': True}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {fee_code} with amount {default_amount}'))
                created_count += 1
            else:
                self.stdout.write(f'Updated existing: {fee_code} (Amount set to: {obj.amount})')
                updated_count += 1
                
        # Clean up any orphaned fees that are no longer in FEE_TYPES
        valid_fee_codes = [code for code, _ in FEE_TYPES]
        orphans = FeeConfiguration.objects.exclude(fee_type__in=valid_fee_codes)
        orphaned_count = orphans.count()
        if orphaned_count > 0:
            orphans.delete()
            self.stdout.write(self.style.WARNING(f'Deleted {orphaned_count} orphaned fee records no longer used in code.'))
                
        self.stdout.write(self.style.SUCCESS(f'Done! Created {created_count} new fees, Updated {updated_count}.'))
