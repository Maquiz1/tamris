import re

def update_forms(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Rename MedicineCategoryIIForm to MasterMedicineApplicationForm
    content = content.replace("class MedicineCategoryIIForm(BaseMedicineForm):", "class MasterMedicineApplicationForm(BaseMedicineForm):")

    # Remove MedicineListingForm class entirely
    # It starts at class MedicineListingForm(BaseMedicineForm):
    # and ends right before class MasterMedicineApplicationForm(BaseMedicineForm):
    pattern = re.compile(r'class MedicineListingForm\(BaseMedicineForm\):.*?class MasterMedicineApplicationForm', re.DOTALL)
    content = pattern.sub('class MasterMedicineApplicationForm', content)

    # We want to add custom logic in MasterMedicineApplicationForm.__init__
    # So we'll inject an __init__ method into MasterMedicineApplicationForm
    
    init_code = """class MasterMedicineApplicationForm(BaseMedicineForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app_type = getattr(self.instance, 'application_type', None)
        
        # Define fields that are exclusively for Category II
        cat2_only_fields = [
            'shelf_life', 'dosage', 'quality_control_procedures', 
            'in_process_control_procedures', 'manufacturing_flow_chart',
            'brela_registration_name', 'scientific_name_report', 
            'heavy_metals_report', 'pesticides_report', 'toxic_chemicals_report', 
            'conventional_drugs_report', 'foreign_matter_report', 'microbes_report', 
            'aflatoxin_report', 'toxicity_report', 'stability_report', 
            'moisture_analysis_report', 'ph_analysis_report', 
            'uniformity_test_report', 'dissolution_test_report', 
            'clinical_observation_report'
        ]
        
        # Define fields that are exclusively for Listing
        listing_only_fields = [
            'other_appearance_instructions'
            # (Note: we leave medicine_color etc available for listing per user prompt)
        ]
        
        if app_type == 'LISTING':
            for f in cat2_only_fields:
                if f in self.fields:
                    self.fields[f].required = False
        elif app_type == 'CATEGORY_II':
            for f in listing_only_fields:
                if f in self.fields:
                    self.fields[f].required = False
                    
"""
    
    content = content.replace("class MasterMedicineApplicationForm(BaseMedicineForm):", init_code)
    
    with open(filename, 'w') as f:
        f.write(content)

update_forms('medicines/forms/applications.py')
