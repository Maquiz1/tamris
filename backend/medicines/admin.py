from django.contrib import admin

from medicines.models import NumberSequence, SystemSettings


@admin.register(NumberSequence)
class NumberSequenceAdmin(admin.ModelAdmin):
    list_display = ('kind', 'year', 'last_number', 'updated_at')
    list_filter = ('kind', 'year')


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'updated_at')
