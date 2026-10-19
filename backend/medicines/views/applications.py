from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from medicines.forms import MasterMedicineApplicationForm, InitiateApplicationForm
from medicines.models import MedicineApplication, FeeConfiguration, FeeInactiveError, MedicineLabelAttachment, SystemSettings
from medicines import services
from users.emails import notify_applicant_application_status

FEE_FOR_START = {'LISTING': 'LISTING_APP_FEE', 'CATEGORY_II': 'CAT_II_APP_FEE'}


@login_required
def initiate_application_view(request, app_type):
    if request.user.registration_status != 'VERIFIED':
        messages.error(request, 'Your account must be verified before you can apply.')
        return redirect('users:dashboard')
    if app_type not in FEE_FOR_START:
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = InitiateApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            application.application_type = app_type
            application.status = 'PENDING_APPLICATION_FEE'
            try:
                FeeConfiguration.get_fee(FEE_FOR_START[app_type])
            except FeeInactiveError:
                messages.error(request, 'New applications are currently suspended because the Application Fee is inactive.')
                return redirect('users:dashboard')
            application.save()
            services.assign_reference(application)
            services.create_fee(application, 'application')
            messages.success(request, f'Application {application.reference_number} started. Please pay the Application Fee (Ada ya maombi) and submit the control number.')
            return redirect('users:dashboard')
    else:
        form = InitiateApplicationForm()
    try:
        fee_amount = FeeConfiguration.get_fee(FEE_FOR_START[app_type], 0.0)
        fee_obj = FeeConfiguration.objects.get(fee_type=FEE_FOR_START[app_type])
    except FeeInactiveError:
        messages.error(request, 'New applications are currently suspended. Please try again later.')
        return redirect('users:dashboard')
    return render(request, 'medicines/initiate_application.html', {'app_type': app_type, 'form': form, 'fee_amount': fee_amount, 'fee_obj': fee_obj})


def _save_label_attachments(request, application):
    for f in request.FILES.getlist('sample_label'):
        MedicineLabelAttachment.objects.create(application=application, file=f)


@login_required
def medicine_master_apply_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if application.status != 'DRAFT':
        messages.error(request, 'Application fee must be verified before filling the form.')
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = MasterMedicineApplicationForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            stage_fee = 'LISTING_EVAL_FEE' if application.application_type == 'LISTING' else 'CAT_II_EVAL_FEE'
            try:
                FeeConfiguration.get_fee(stage_fee)
            except FeeInactiveError:
                messages.error(request, 'Cannot submit application because the Evaluation Fee is currently suspended.')
                return redirect('users:dashboard')
            app = form.save(commit=False)
            app.status = 'PENDING_EVALUATION_FEE'
            app.submitted_at = timezone.now()
            app.save()
            _save_label_attachments(request, app)
            services.assign_reference(app)
            services.create_fee(app, 'evaluation')
            notify_applicant_application_status(
                app,
                'TAMRIS - Application Submitted Successfully',
                'Your application has been received.\n'
                'Please pay the Evaluation Fee (Ada ya tathmini) and submit the control number to proceed.'
            )
            messages.success(request, 'Application submitted. Please pay the Evaluation Fee (Ada ya tathmini) and submit the control number.')
            return redirect('users:dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = MasterMedicineApplicationForm(instance=application)

    return render(request, 'medicines/apply_master.html', {'form': form, 'application': application})


@login_required
def medicine_application_edit_view(request, pk):
    """The applicant corrects the sections opened by Conditions for Improvement."""
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if application.status != 'CONDITIONS_APPLIED':
        messages.error(request, 'This application is not currently open for edits.')
        return redirect('users:dashboard')
    if request.method == 'POST':
        form = MasterMedicineApplicationForm(request.POST, request.FILES, instance=application)
        if form.is_valid():
            app = form.save()
            _save_label_attachments(request, app)
            services.resubmit_after_conditions(app)
            messages.success(request, 'Your corrected application has been resubmitted for review.')
            return redirect('users:dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = MasterMedicineApplicationForm(instance=application)
    return render(request, 'medicines/apply_master.html', {'form': form, 'application': application, 'is_edit': True})


def _document_context(application):
    return {'application': application, 'settings_obj': SystemSettings.load()}


@login_required
def certificate_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk)
    if application.applicant_id != request.user.id and not request.user.is_staff_member:
        return redirect('users:dashboard')
    if not services.can_view_certificate(request.user, application):
        messages.error(request, 'The certificate is not available for this application.')
        return redirect('users:dashboard')
    if application.shows_original_scan:
        return redirect(application.legacy_certificate_scan.url)
    template = 'medicines/documents/certificate_listing.html' if application.is_listing else 'medicines/documents/certificate_registration.html'
    return render(request, template, _document_context(application))


@login_required
def provisional_letter_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk)
    if application.applicant_id != request.user.id and not request.user.is_staff_member:
        return redirect('users:dashboard')
    if not services.can_view_provisional(request.user, application):
        if application.applicant_id == request.user.id and application.has_active_certificate:
            messages.info(request, 'Your certificate has been issued, so the provisional letter is no longer available. Please download the certificate instead.')
        else:
            messages.error(request, 'The provisional letter is not available for this application.')
        return redirect('users:dashboard')
    template = 'medicines/documents/provisional_listing.html' if application.is_listing else 'medicines/documents/provisional_registration.html'
    return render(request, template, _document_context(application))


@login_required
def start_renewal_view(request, pk):
    application = get_object_or_404(MedicineApplication, pk=pk, applicant=request.user)
    if request.method != 'POST':
        raise Http404
    try:
        payment = services.start_renewal(application)
    except services.WorkflowError as e:
        messages.error(request, str(e))
        return redirect('medicines:applicant_certificate_list')
    except FeeInactiveError:
        messages.error(request, 'Renewals are currently suspended because the Renewal Fee is inactive.')
        return redirect('medicines:applicant_certificate_list')
    messages.success(request, f'Renewal started. Please pay the {payment.get_payment_type_display()} and submit the control number.')
    return redirect('medicines:submit_payment', pk=payment.pk)


# Fields copied when a listed medicine is upgraded to a Category II application.
UPGRADE_COPY_FIELDS = [
    'traditional_medicine_skills', 'traditional_medicine_skills_other',
    'training_institution', 'training_duration', 'training_duration_type',
    'inherited_from', 'inherited_duration', 'inherited_duration_type',
    'medicine_name', 'dosage_form', 'dosage_form_other', 'empty_packaging_size',
    'net_weight_volume', 'net_weight_volume_unit',
    'medicine_color', 'medicine_smell', 'medicine_taste', 'medicine_texture',
    'packaging_size', 'packaging_color', 'lid_color', 'other_appearance_instructions',
    'ingredients_table', 'active_ingredients', 'excipients', 'ingredients',
    'route_of_administration', 'route_of_administration_other',
    'indications', 'directions_for_use', 'known_side_effects', 'possible_side_effects',
    'precautions', 'instructions_for_use', 'storage_conditions', 'storage_conditions_other',
    'shelf_life', 'shelf_life_duration_type',
    'local_harvest_season', 'local_harvested_part', 'local_harvested_part_other',
    'local_cultivated_or_wild', 'local_abundance',
    'foreign_source_countries', 'foreign_harvest_season', 'foreign_harvested_part',
    'foreign_harvested_part_other', 'foreign_cultivated_or_wild', 'foreign_abundance',
    'harvesting_method', 'does_dry_raw_materials', 'drying_area', 'drying_equipment',
    'manufacturing_location_type', 'manufacturing_area_size', 'manufacturing_procedures',
    'equipment_used', 'manufacturing_area', 'packaging_procedures',
    'manufacturer_name', 'manufacturer_address',
]


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
        status__in=['FULL_REGISTRATION', 'PROVISIONAL_REGISTRATION'],
    )

    if request.method != 'POST':
        messages.error(request, 'Invalid request method for upgrade.')
        return redirect('users:dashboard')

    try:
        FeeConfiguration.get_fee('CAT_II_APP_FEE')
    except FeeInactiveError:
        messages.error(request, 'Upgrade suspended because the Category II Application Fee is inactive.')
        return redirect('users:dashboard')

    # Category II specific fields and uploads are left empty on purpose, so they are entered fresh.
    new_app = MedicineApplication(
        applicant=request.user,
        application_type='CATEGORY_II',
        status='PENDING_APPLICATION_FEE',
        **{field: getattr(old_app, field) for field in UPGRADE_COPY_FIELDS},
    )
    new_app.save()
    services.assign_reference(new_app)
    services.create_fee(new_app, 'application')
    messages.success(request, f'Upgrade started as {new_app.reference_number}. Please pay the Application Fee for {new_app.medicine_name}.')
    return redirect('users:dashboard')
