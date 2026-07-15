from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from medicines.forms import MedicineListingForm, MedicineCategoryIIForm, PreliminaryEvaluationForm, ScientificEvaluationForm, PaymentVerificationForm, ApplicantPaymentSubmissionForm, FeeConfigurationForm, InitiateApplicationForm, InspectionScheduleForm, InspectionReportForm
from django.utils import timezone
from medicines.models import MedicineApplication, MedicineEvaluation, Payment, FeeConfiguration, InspectionSchedule, FeeInactiveError
from django.core.paginator import Paginator
from django.db.models import Q
from users.emails import notify_finance_pending_payment, notify_evaluator_payment_verified, notify_applicant_application_status

def get_filtered_applications(request, base_queryset):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    if query:
        if query in ['LISTING', 'CATEGORY_II']:
            base_queryset = base_queryset.filter(application_type=query)
        else:
            base_queryset = base_queryset.filter(Q(medicine_name__icontains=query) | Q(applicant__email__icontains=query) | Q(applicant__user_profile__first_name__icontains=query) | Q(applicant__user_profile__last_name__icontains=query) | Q(applicant__company_profile__company_name__icontains=query)).distinct()
    if status_filter:
        base_queryset = base_queryset.filter(status=status_filter)
    if start_date:
        base_queryset = base_queryset.filter(submitted_at__date__gte=start_date)
    if end_date:
        base_queryset = base_queryset.filter(submitted_at__date__lte=end_date)
    return (base_queryset, query, status_filter, start_date, end_date)
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth