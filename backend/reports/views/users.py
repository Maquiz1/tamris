from reports.views.utils import is_staff_check, export_csv
import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import models
from medicines.models import MedicineApplication, Payment, MedicineEvaluation, InspectionSchedule
from users.models import CustomUser

@login_required
@user_passes_test(is_staff_check)
def users_report_view(request):
    qs = CustomUser.objects.all().order_by('-date_joined')
    if request.GET.get('export') == 'csv':
        fields = [{'name': 'id', 'label': 'ID'}, {'name': 'email', 'label': 'Email'}, {'name': 'phone_number', 'label': 'Phone'}, {'name': 'is_staff', 'label': 'Is Staff'}, {'name': 'date_joined', 'label': 'Date Joined'}]
        return export_csv(qs, 'users_report', fields)
    return render(request, 'reports/users.html', {'users': qs})