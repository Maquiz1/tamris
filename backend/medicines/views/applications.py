from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from medicines.forms import MasterMedicineApplicationForm, PreliminaryEvaluationForm, ScientificEvaluationForm, PaymentVerificationForm, ApplicantPaymentSubmissionForm, FeeConfigurationForm, InitiateApplicationForm, InspectionScheduleForm, InspectionReportForm
from django.utils import timezone
from medicines.models import MedicineApplication, MedicineEvaluation, Payment, FeeConfiguration, InspectionSchedule, FeeInactiveError
from django.core.paginator import Paginator
from django.db.models import Q
from users.emails import notify_finance_pending_payment, notify_evaluator_payment_verified, notify_applicant_application_status

@login_required
def initiate_application_view(request, app_type):
    if request.user.registration_status != 'VERIFIED':
        messages.error(request, 'Your account must be verified before you can apply.')
        return redirect('users:dashboard')
    if app_type not in ['LISTING', 'CATEGORY_II']:
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = InitiateApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            application.application_type = app_type
            application.status = 'PENDING_APPLICATION_FEE'
            application.save()
            try:
                if app_type == 'LISTING':
                    fee_amount = FeeConfiguration.get_fee('LISTING_APP_FEE', 50000.0)
                    payment_code = 'LISTING_APP_FEE'
                else:
                    fee_amount = FeeConfiguration.get_fee('CAT_II_APP_FEE', 100000.0)
                    payment_code = 'CAT_II_APP_FEE'
                Payment.objects.create(application=application, payment_type=payment_code, amount=fee_amount)
                messages.success(request, 'Application initiated. Please submit your Application Fee (Ada ya maombi) receipt.')
                return redirect('users:dashboard')
            except FeeInactiveError as e:
                application.delete()
                messages.error(request, 'New applications are currently suspended because the Application Fee is inactive.')
                return redirect('users:dashboard')
    else:
        form = InitiateApplicationForm()
    try:
        if app_type == 'LISTING':
            fee_amount = FeeConfiguration.get_fee('LISTING_APP_FEE', 0.0)
            fee_obj = FeeConfiguration.objects.get(fee_type='LISTING_APP_FEE')
        else:
            fee_amount = FeeConfiguration.get_fee('CAT_II_APP_FEE', 0.0)
            fee_obj = FeeConfiguration.objects.get(fee_type='CAT_II_APP_FEE')
    except FeeInactiveError:
        messages.error(request, 'New applications are currently suspended. Please try again later.')
        return redirect('users:dashboard')
    return render(request, 'medicines/initiate_application.html', {'app_type': app_type, 'form': form, 'fee_amount': fee_amount, 'fee_obj': fee_obj})

@login_required
def medicine_master_apply_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if application.status != 'DRAFT':
        messages.error(request, 'Application fee must be verified before filling the form.')
        return redirect('users:dashboard')
        
    if request.method == 'POST':
        form = MasterMedicineApplicationForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            app = form.save(commit=False)
            app.status = 'PENDING_EVALUATION_FEE'
            app.submitted_at = timezone.now()
            app.save()
            
            # Determine fee based on application type
            try:
                if app.application_type == 'LISTING':
                    fee_type = 'LISTING_EVAL_FEE'
                    fee_amount = FeeConfiguration.get_fee(fee_type, 150000.0)
                else:
                    fee_type = 'CAT_II_EVAL_FEE'
                    fee_amount = FeeConfiguration.get_fee(fee_type, 300000.0)
                    
                Payment.objects.create(application=app, payment_type=fee_type, amount=fee_amount)
                notify_applicant_application_status(
                    app, 
                    'TAMRIS - Application Submitted Successfully', 
                    'Your application has been received.\n'
                    'Please submit your Evaluation Fee (Ada ya tathmini) receipt to proceed.'
                )
                messages.success(request, 'Application submitted. Please submit your Evaluation Fee (Ada ya tathmini) receipt.')
                return redirect('users:dashboard')
            except FeeInactiveError:
                app.status = 'DRAFT'
                app.save()
                messages.error(request, 'Cannot submit application because the Evaluation Fee is currently suspended.')
                return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MasterMedicineApplicationForm(instance=application)
        
    return render(request, 'medicines/apply_master.html', {'form': form, 'application': application})

@login_required
def medicine_application_edit_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if application.status != 'CONDITIONS_APPLIED':
        messages.error(request, 'This application is not currently open for edits.')
        return redirect('users:dashboard')
    if application.application_type == 'LISTING':
        form_class = MasterMedicineApplicationForm
        template_name = 'medicines/apply_master.html'
    else:
        form_class = MasterMedicineApplicationForm
        template_name = 'medicines/apply_master.html'
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=application)
        if form.is_valid():
            app = form.save(commit=False)
            app.status = 'UNDER_REVIEW'
            app.submitted_at = timezone.now()
            app.save()
            messages.success(request, 'Your corrected application has been resubmitted for review.')
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = form_class(instance=application)
    return render(request, template_name, {'form': form, 'is_edit': True})

@login_required
def certificate_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk)
    if not (request.user == application.applicant or request.user.is_staff_member):
        return redirect('users:dashboard')
    if application.status not in ['FULL_REGISTRATION', 'PROVISIONAL_REGISTRATION', 'PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE', 'PENDING_FINAL_APPROVAL']:
        messages.error(request, 'Certificate or Provisional Letter is not yet available for this application.')
        return redirect('users:dashboard')
    return render(request, 'medicines/certificate.html', {'application': application})
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth

@login_required
def upgrade_to_registration_view(request, pk):
    if request.user.registration_status != 'VERIFIED':
        messages.error(request, 'Your account must be verified before you can apply.')
        return redirect('users:dashboard')
        
    old_app = get_object_or_404(
        MedicineApplication, 
        pk=pk, 
        applicant=request.user, 
        application_type='LISTING',
        status__in=['FULL_REGISTRATION', 'PROVISIONAL_REGISTRATION']
    )
    
    if request.method == 'POST':
        # Create a new application and clone fields
        new_app = MedicineApplication(
            applicant=request.user,
            application_type='CATEGORY_II',
            status='PENDING_APPLICATION_FEE',
            # Copy text and simple fields
            traditional_medicine_skills=old_app.traditional_medicine_skills,
            training_institution=old_app.training_institution,
            training_duration=old_app.training_duration,
            training_duration_type=old_app.training_duration_type,
            inherited_from=old_app.inherited_from,
            inherited_duration=old_app.inherited_duration,
            inherited_duration_type=old_app.inherited_duration_type,
            traditional_medicine_skills_other=old_app.traditional_medicine_skills_other,
            medicine_name=old_app.medicine_name,
            dosage_form=old_app.dosage_form,
            net_weight_volume=old_app.net_weight_volume,
            medicine_color=old_app.medicine_color,
            medicine_smell=old_app.medicine_smell,
            medicine_taste=old_app.medicine_taste,
            medicine_texture=old_app.medicine_texture,
            packaging_size=old_app.packaging_size,
            packaging_color=old_app.packaging_color,
            lid_color=old_app.lid_color,
            other_appearance_instructions=old_app.other_appearance_instructions,
            ingredients_table=old_app.ingredients_table,
            active_ingredients=old_app.active_ingredients,
            excipients=old_app.excipients,
            ingredients=old_app.ingredients,
            route_of_administration=old_app.route_of_administration,
            indications=old_app.indications,
            directions_for_use=old_app.directions_for_use,
            possible_side_effects=old_app.possible_side_effects,
            precautions=old_app.precautions,
            instructions_for_use=old_app.instructions_for_use,
            storage_conditions=old_app.storage_conditions,
            local_harvest_season=old_app.local_harvest_season,
            local_harvested_part=old_app.local_harvested_part,
            local_cultivated_or_wild=old_app.local_cultivated_or_wild,
            local_abundance=old_app.local_abundance,
            imported_countries=old_app.imported_countries,
            imported_plant_part=old_app.imported_plant_part,
            imported_raw_state=old_app.imported_raw_state,
            imported_abundance=old_app.imported_abundance,
            harvesting_method=old_app.harvesting_method,
            drying_procedures=old_app.drying_procedures,
            drying_area=old_app.drying_area,
            drying_equipment=old_app.drying_equipment,
            manufacturing_location_type=old_app.manufacturing_location_type,
            manufacturing_area_size=old_app.manufacturing_area_size,
            manufacturing_procedures=old_app.manufacturing_procedures,
            equipment_used=old_app.equipment_used,
            manufacturing_area=old_app.manufacturing_area,
            packaging_procedures=old_app.packaging_procedures,
            # (intentionally omitting Category II specific fields and file uploads to force re-entry/upload)
        )
        new_app.save()
        
        try:
            fee_amount = FeeConfiguration.get_fee('CAT_II_APP_FEE', 100000.0)
            Payment.objects.create(application=new_app, payment_type='CAT_II_APP_FEE', amount=fee_amount)
            messages.success(request, f'Upgrade initiated. Please submit your Application Fee receipt for {new_app.medicine_name}.')
            return redirect('users:dashboard')
        except FeeInactiveError:
            new_app.delete()
            messages.error(request, 'Upgrade suspended because the Category II Application Fee is inactive.')
            return redirect('users:dashboard')
            
    # If GET, you could confirm the upgrade, or just do it. But generally a POST is safer for creation.
    # Given we might be doing this via a form POST in the template, we'll assume it handles both.
    messages.error(request, 'Invalid request method for upgrade.')
    return redirect('users:dashboard')