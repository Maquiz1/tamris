import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import models
from medicines.models import MedicineApplication, Payment, MedicineEvaluation, InspectionSchedule
from users.models import CustomUser

def is_staff_check(user):
    return user.is_active and (user.is_staff or getattr(user, 'is_staff_member', False))

def export_csv(queryset, filename, fields):
    """Helper function to export a queryset to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'''attachment; filename="{filename}_{timezone.now().strftime('%Y%m%d')}.csv"'''
    writer = csv.writer(response)
    writer.writerow([field['label'] for field in fields])
    for obj in queryset:
        row = []
        for field in fields:
            val = getattr(obj, field['name'], '')
            if callable(val):
                val = val()
            row.append(val)
        writer.writerow(row)
    return response