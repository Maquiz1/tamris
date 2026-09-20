import re

def update_views(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Imports
    content = content.replace(
        "from medicines.forms import MedicineListingForm, MedicineCategoryIIForm,",
        "from medicines.forms import MasterMedicineApplicationForm,"
    )

    # We want to replace `medicine_listing_apply_view` and `medicine_category_ii_apply_view` with `medicine_master_apply_view`.
    # First, let's find the start of `medicine_listing_apply_view` and the end of `medicine_category_ii_apply_view`
    pattern = re.compile(r'@login_required\ndef medicine_listing_apply_view\(.*?\n@login_required\ndef medicine_application_edit_view', re.DOTALL)
    
    master_view = """@login_required
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
                    'Your application has been received.\\nPlease submit your Evaluation Fee (Ada ya tathmini) receipt to proceed.'
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
def medicine_application_edit_view"""

    content = pattern.sub(master_view, content)
    
    # Also update edit view to use MasterMedicineApplicationForm
    content = content.replace("form_class = MedicineListingForm\n        template_name = 'medicines/apply_listing.html'", "form_class = MasterMedicineApplicationForm\n        template_name = 'medicines/apply_master.html'")
    content = content.replace("form_class = MedicineCategoryIIForm\n        template_name = 'medicines/apply_category_ii.html'", "form_class = MasterMedicineApplicationForm\n        template_name = 'medicines/apply_master.html'")

    with open(filename, 'w') as f:
        f.write(content)

update_views('medicines/views/applications.py')
