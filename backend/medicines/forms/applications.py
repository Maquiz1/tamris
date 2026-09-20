from django import forms
from medicines.models import MedicineApplication

class BaseMedicineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.status == 'CONDITIONS_APPLIED':
            try:
                allowed_sections = self.instance.evaluation.sections_to_revise
            except Exception:
                allowed_sections = []
                
            field_mapping = {
                'application_type': 'BASIC_DETAILS',
                'medicine_name': 'BASIC_DETAILS', 'dosage_form': 'BASIC_DETAILS', 'dosage_form_other': 'BASIC_DETAILS', 'indications': 'BASIC_DETAILS',
                'directions_for_use': 'BASIC_DETAILS', 'possible_side_effects': 'BASIC_DETAILS', 'precautions': 'BASIC_DETAILS',
                'instructions_for_use': 'BASIC_DETAILS', 'storage_conditions': 'BASIC_DETAILS', 'empty_packaging_size': 'BASIC_DETAILS', 'net_weight_volume': 'BASIC_DETAILS',
                'medicine_color': 'BASIC_DETAILS', 'medicine_smell': 'BASIC_DETAILS', 'medicine_taste': 'BASIC_DETAILS',
                'medicine_texture': 'BASIC_DETAILS', 'packaging_size': 'BASIC_DETAILS', 'packaging_color': 'BASIC_DETAILS',
                'lid_color': 'BASIC_DETAILS', 'other_appearance_instructions': 'BASIC_DETAILS', 'route_of_administration': 'BASIC_DETAILS',
                'traditional_medicine_skills': 'BASIC_DETAILS', 'traditional_medicine_skills_other': 'BASIC_DETAILS',
                'training_institution': 'BASIC_DETAILS', 'training_duration': 'BASIC_DETAILS', 'training_duration_type': 'BASIC_DETAILS',
                'inherited_from': 'BASIC_DETAILS', 'inherited_duration': 'BASIC_DETAILS', 'inherited_duration_type': 'BASIC_DETAILS',
                
                'ingredients': 'INGREDIENTS', 'ingredients_table': 'INGREDIENTS', 'active_ingredients': 'INGREDIENTS', 'excipients': 'INGREDIENTS',
                'local_harvest_season': 'INGREDIENTS', 'local_harvested_part': 'INGREDIENTS', 'local_harvested_part_other': 'INGREDIENTS',
                'local_cultivated_or_wild': 'INGREDIENTS', 'local_abundance': 'INGREDIENTS', 'foreign_source_countries': 'INGREDIENTS',
                'foreign_harvest_season': 'INGREDIENTS', 'foreign_harvested_part': 'INGREDIENTS', 'foreign_harvested_part_other': 'INGREDIENTS',
                'foreign_cultivated_or_wild': 'INGREDIENTS', 'foreign_abundance': 'INGREDIENTS',
                
                'does_dry_raw_materials': 'MANUFACTURING', 'drying_area': 'MANUFACTURING', 'drying_equipment': 'MANUFACTURING',
                'manufacturing_location_type': 'MANUFACTURING', 'manufacturing_area_size': 'MANUFACTURING', 'manufacturing_area': 'MANUFACTURING',
                'manufacturing_procedures': 'MANUFACTURING', 'harvesting_method': 'MANUFACTURING', 'equipment_used': 'MANUFACTURING',
                'packaging_procedures': 'MANUFACTURING',
                
                'sample_label': 'DOCUMENTS', 'statement_of_efficacy': 'DOCUMENTS', 'literature_review': 'DOCUMENTS',
                'tahpc_certificate': 'DOCUMENTS', 'ingredients_info_doc': 'DOCUMENTS', 'medicine_photos': 'DOCUMENTS',
                'instructions_doc': 'DOCUMENTS', 'ph_analysis_report': 'DOCUMENTS', 'uniformity_test_report': 'DOCUMENTS',
                'dissolution_test_report': 'DOCUMENTS', 'clinical_observation_report': 'DOCUMENTS',
            }
            
            for field_name, field in self.fields.items():
                section = field_mapping.get(field_name)
                if section not in allowed_sections:
                    field.disabled = True
                    field.widget.attrs['readonly'] = True
                    # Remove the required attribute for disabled fields so the form can still submit valid data
                    field.required = False

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)] if data else []
        return result

class MasterMedicineApplicationForm(BaseMedicineForm):
    sample_label = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf', 'multiple': True}),
        label="Sample medicine label (Mfano wa lebo ya dawa)",
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        app_type = getattr(self.instance, 'application_type', None)
        
        # Define fields that are exclusively for Category II
        cat2_only_fields = [
            'shelf_life', 'shelf_life_duration_type', 'dosage', 'quality_control_procedures', 'storage_environment',
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
                    

    class Meta:
        model = MedicineApplication
        fields = [
            'medicine_name', 
            'dosage_form', 
            'dosage_form_other',
            'indications', 
            'ingredients',
            'traditional_medicine_skills', 'traditional_medicine_skills_other',
            'training_institution', 'training_duration', 'training_duration_type', 'inherited_from', 'inherited_duration', 'inherited_duration_type',
            'empty_packaging_size', 'net_weight_volume', 'medicine_color', 'medicine_smell', 'medicine_taste', 'medicine_texture',
            'packaging_size', 'packaging_color', 'lid_color', 'other_appearance_instructions',
            'ingredients_table', 'active_ingredients', 'excipients',
            'route_of_administration', 'route_of_administration_other',
            'local_harvest_season', 'local_harvested_part', 'local_harvested_part_other', 'local_cultivated_or_wild', 'local_abundance', 'foreign_source_countries',
            'foreign_harvest_season', 'foreign_harvested_part', 'foreign_harvested_part_other', 'foreign_cultivated_or_wild', 'foreign_abundance',
            'does_dry_raw_materials', 'drying_area', 'drying_equipment',
            'manufacturing_location_type', 'manufacturing_area_size', 'manufacturing_area',
            'manufacturing_procedures', 'harvesting_method', 'equipment_used', 'packaging_procedures',
            
            'directions_for_use',
            'known_side_effects',
            'possible_side_effects',
            'precautions',
            'instructions_for_use',
            'storage_conditions', 'storage_conditions_other',
            'shelf_life', 'shelf_life_duration_type',
            'dosage',
            
            'quality_control_procedures', 'storage_environment',
            'in_process_control_procedures',
            'manufacturing_flow_chart',

            # Category II specific file fields
            'scientific_name_report',
            'heavy_metals_report',
            'pesticides_report',
            'toxic_chemicals_report',
            'conventional_drugs_report',
            'foreign_matter_report',
            'microbes_report',
            'aflatoxin_report',
            'toxicity_report',
            'stability_report',
            'moisture_analysis_report',
            'ph_analysis_report',
            'uniformity_test_report',
            'dissolution_test_report',
            'clinical_observation_report',
            'brela_registration_name',
            
            # Common file fields
            'statement_of_efficacy',
            'literature_review',
            'tahpc_certificate',
            'ingredients_info_doc',
            'medicine_photos',
            'instructions_doc',
        ]
        widgets = {
            'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter medicine name', 'readonly': 'readonly'}),
            'dosage_form': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleDosageFormOther()'}),
            'dosage_form_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify'}),
            'indications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What is this medicine used to treat?'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List of raw materials or herbs used'}),
            'directions_for_use': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How should the medicine be used/applied?'}),
            'known_side_effects': forms.RadioSelect(choices=[(True, 'Ndiyo'), (False, 'Hapana')], attrs={'class': 'form-check-input', 'onchange': 'toggleSideEffects()'}),
            'possible_side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are the possible side effects?'}),
            'precautions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any precautions to take before/during use?'}),
            'instructions_for_use': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Specific instructions for use'}),
            'storage_conditions': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleStorageConditionsOther()'}),
            'storage_conditions_other': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Elezea mazingira maalum'}),
            'shelf_life': forms.NumberInput(attrs={'class': 'form-control'}),
            'shelf_life_duration_type': forms.Select(attrs={'class': 'form-select'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2 tablets twice a day, 5ml every 8 hours'}),
            
            # Skills
            'traditional_medicine_skills': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'traditional_medicine_skills_other': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'training_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'training_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'training_duration_type': forms.Select(attrs={'class': 'form-select'}),
            'inherited_from': forms.TextInput(attrs={'class': 'form-control'}),
            'inherited_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'inherited_duration_type': forms.Select(attrs={'class': 'form-select'}),
            
            # Appearance
            'empty_packaging_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'net_weight_volume': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'medicine_color': forms.TextInput(attrs={'class': 'form-control'}),
            'medicine_smell': forms.TextInput(attrs={'class': 'form-control'}),
            'medicine_taste': forms.TextInput(attrs={'class': 'form-control'}),
            'medicine_texture': forms.TextInput(attrs={'class': 'form-control'}),
            'packaging_size': forms.TextInput(attrs={'class': 'form-control'}),
            'packaging_color': forms.TextInput(attrs={'class': 'form-control'}),
            'lid_color': forms.TextInput(attrs={'class': 'form-control'}),
            'other_appearance_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            
            # Ingredients
            'ingredients_table': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List ingredients (Kiswahili/English/Latin names, source, part used)'}),
            'active_ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'excipients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            # Route
            'route_of_administration': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleRouteOther()'}),
            'route_of_administration_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify'}),
            
            # Sources
            'local_harvest_season': forms.Select(attrs={'class': 'form-select'}),
            'local_harvested_part': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleHarvestedPartOther()'}),
            'local_harvested_part_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify'}),
            'local_cultivated_or_wild': forms.Select(attrs={'class': 'form-select'}),
            'local_abundance': forms.Select(attrs={'class': 'form-select'}),
            'foreign_source_countries': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Kenya, India'}),
            'foreign_harvest_season': forms.Select(attrs={'class': 'form-select'}),
            'foreign_harvested_part': forms.Select(attrs={'class': 'form-select'}),
            'foreign_harvested_part_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify'}),
            'foreign_cultivated_or_wild': forms.Select(attrs={'class': 'form-select'}),
            'foreign_abundance': forms.Select(attrs={'class': 'form-select'}),
            
            # Manufacturing Info
            'harvesting_method': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe how raw materials are harvested'}),
            'does_dry_raw_materials': forms.RadioSelect(choices=[(True, 'Ndiyo'), (False, 'Hapana')], attrs={'class': 'form-check-input', 'onchange': 'toggleDryingFields()'}),
            'drying_area': forms.TextInput(attrs={'class': 'form-control'}),
            'drying_equipment': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturing_location_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'manufacturing_area_size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 50.5'}),
            'manufacturing_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide step-by-step manufacturing procedures'}),
            'equipment_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List all equipment used in production'}),
            'manufacturing_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where is the medicine manufactured?'}),
            'packaging_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe how the final product is packaged'}),
            'quality_control_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Quality control procedures'}),
            'storage_environment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mazingira ya utunzaji'}),
            'in_process_control_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'In-process control procedures'}),
            'manufacturing_flow_chart': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
            
            # Category II Specific
            'brela_registration_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'BRELA Registered Name (if any)'}),
            'scientific_name_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'heavy_metals_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'pesticides_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'toxic_chemicals_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'conventional_drugs_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'foreign_matter_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'microbes_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'aflatoxin_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'toxicity_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'stability_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'moisture_analysis_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'ph_analysis_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'uniformity_test_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'dissolution_test_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'clinical_observation_report': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),

            # Attachments
            'statement_of_efficacy': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'literature_review': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'tahpc_certificate': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
            'ingredients_info_doc': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'medicine_photos': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'instructions_doc': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }

class InitiateApplicationForm(forms.ModelForm):
    class Meta:
        model = MedicineApplication
        fields = ['medicine_name']
        widgets = {
            'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the exact name of your medicine'})
        }

    def clean_medicine_name(self):
        medicine_name = self.cleaned_data.get('medicine_name')
        if MedicineApplication.objects.filter(medicine_name__iexact=medicine_name).exists():
            raise forms.ValidationError("A medicine with this name already exists or is currently being processed.")
        return medicine_name

