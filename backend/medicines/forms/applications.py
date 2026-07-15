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
                'medicine_name': 'BASIC_DETAILS', 'dosage_form': 'BASIC_DETAILS', 'indications': 'BASIC_DETAILS',
                'directions_for_use': 'BASIC_DETAILS', 'possible_side_effects': 'BASIC_DETAILS', 'precautions': 'BASIC_DETAILS',
                'instructions_for_use': 'BASIC_DETAILS', 'storage_conditions': 'BASIC_DETAILS', 'net_weight_volume': 'BASIC_DETAILS',
                'medicine_color': 'BASIC_DETAILS', 'medicine_smell': 'BASIC_DETAILS', 'medicine_taste': 'BASIC_DETAILS',
                'medicine_texture': 'BASIC_DETAILS', 'packaging_size': 'BASIC_DETAILS', 'packaging_color': 'BASIC_DETAILS',
                'lid_color': 'BASIC_DETAILS', 'other_appearance_instructions': 'BASIC_DETAILS', 'route_of_administration': 'BASIC_DETAILS',
                'traditional_medicine_skills': 'BASIC_DETAILS', 'skills_acquired_details': 'BASIC_DETAILS',
                
                'ingredients': 'INGREDIENTS', 'ingredients_table': 'INGREDIENTS', 'active_ingredients': 'INGREDIENTS', 'excipients': 'INGREDIENTS',
                'local_harvest_season': 'INGREDIENTS', 'local_harvested_part': 'INGREDIENTS', 'local_cultivated_or_wild': 'INGREDIENTS',
                'local_abundance': 'INGREDIENTS', 'imported_countries': 'INGREDIENTS', 'imported_plant_part': 'INGREDIENTS',
                'imported_raw_state': 'INGREDIENTS', 'imported_abundance': 'INGREDIENTS',
                
                'drying_area': 'MANUFACTURING', 'drying_equipment': 'MANUFACTURING', 'drying_procedures': 'MANUFACTURING',
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

class MedicineListingForm(BaseMedicineForm):
    class Meta:
        model = MedicineApplication
        fields = [
            'medicine_name', 
            'dosage_form', 
            'indications', 
            'ingredients',
            'traditional_medicine_skills', 'skills_acquired_details',
            'net_weight_volume', 'medicine_color', 'medicine_smell', 'medicine_taste', 'medicine_texture',
            'packaging_size', 'packaging_color', 'lid_color', 'other_appearance_instructions',
            'ingredients_table', 'active_ingredients', 'excipients',
            'route_of_administration',
            'local_harvest_season', 'local_harvested_part', 'local_cultivated_or_wild', 'local_abundance',
            'imported_countries', 'imported_plant_part', 'imported_raw_state', 'imported_abundance',
            'drying_area', 'drying_equipment', 'drying_procedures',
            'manufacturing_location_type', 'manufacturing_area_size', 'manufacturing_area',
            'manufacturing_procedures', 'harvesting_method', 'equipment_used', 'packaging_procedures',
            
            'directions_for_use',
            'possible_side_effects',
            'precautions',
            'instructions_for_use',
            'storage_conditions',
            
            # Common file fields
            'sample_label',
            'statement_of_efficacy',
            'literature_review',
            'tahpc_certificate',
            'ingredients_info_doc',
            'medicine_photos',
            'instructions_doc',
        ]
        widgets = {
            'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter medicine name', 'readonly': 'readonly'}),
            'dosage_form': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Liquid, Powder, Tablet, Cream'}),
            'indications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What is this medicine used to treat?'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List of raw materials or herbs used'}),
            'directions_for_use': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How should the medicine be used/applied?'}),
            'possible_side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are the possible side effects?'}),
            'precautions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any precautions to take before/during use?'}),
            'instructions_for_use': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Specific instructions for use'}),
            'storage_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How should the medicine be stored? (e.g. Keep in a cool, dry place)'}),
            
            # Skills
            'traditional_medicine_skills': forms.Select(attrs={'class': 'form-select'}),
            'skills_acquired_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Provide details on how you acquired these skills'}),
            
            # Appearance
            'net_weight_volume': forms.TextInput(attrs={'class': 'form-control'}),
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
            'route_of_administration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Oral, External, Inhale...'}),
            
            # Sources
            'local_harvest_season': forms.TextInput(attrs={'class': 'form-control'}),
            'local_harvested_part': forms.TextInput(attrs={'class': 'form-control'}),
            'local_cultivated_or_wild': forms.Select(attrs={'class': 'form-select'}),
            'local_abundance': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_countries': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_plant_part': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_raw_state': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_abundance': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Manufacturing Info
            'harvesting_method': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe how raw materials are harvested'}),
            'drying_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the drying process'}),
            'drying_area': forms.TextInput(attrs={'class': 'form-control'}),
            'drying_equipment': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturing_location_type': forms.Select(attrs={'class': 'form-select'}),
            'manufacturing_area_size': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturing_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide step-by-step manufacturing procedures'}),
            'equipment_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List all equipment used in production'}),
            'manufacturing_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where is the medicine manufactured?'}),
            'packaging_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe how the final product is packaged'}),
            
            # Attachments
            'sample_label': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
            'statement_of_efficacy': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'literature_review': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'tahpc_certificate': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
            'ingredients_info_doc': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'medicine_photos': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'instructions_doc': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }

class MedicineCategoryIIForm(BaseMedicineForm):
    class Meta:
        model = MedicineApplication
        fields = [
            'medicine_name', 
            'dosage_form', 
            'indications', 
            'ingredients',
            'traditional_medicine_skills', 'skills_acquired_details',
            'net_weight_volume', 'medicine_color', 'medicine_smell', 'medicine_taste', 'medicine_texture',
            'packaging_size', 'packaging_color', 'lid_color', 'other_appearance_instructions',
            'ingredients_table', 'active_ingredients', 'excipients',
            'route_of_administration',
            'local_harvest_season', 'local_harvested_part', 'local_cultivated_or_wild', 'local_abundance',
            'imported_countries', 'imported_plant_part', 'imported_raw_state', 'imported_abundance',
            'drying_area', 'drying_equipment', 'drying_procedures',
            'manufacturing_location_type', 'manufacturing_area_size', 'manufacturing_area',
            'manufacturing_procedures', 'harvesting_method', 'equipment_used', 'packaging_procedures',
            
            'directions_for_use',
            'possible_side_effects',
            'precautions',
            'instructions_for_use',
            'storage_conditions',
            'shelf_life',
            'dosage',
            
            'quality_control_procedures',
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
            'sample_label',
            'statement_of_efficacy',
            'literature_review',
            'tahpc_certificate',
            'ingredients_info_doc',
            'medicine_photos',
            'instructions_doc',
        ]
        widgets = {
            'medicine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter medicine name', 'readonly': 'readonly'}),
            'dosage_form': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Liquid, Powder, Tablet, Cream'}),
            'indications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What is this medicine used to treat?'}),
            'ingredients': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List of raw materials or herbs used'}),
            'directions_for_use': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How should the medicine be used/applied?'}),
            'possible_side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are the possible side effects?'}),
            'precautions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any precautions to take before/during use?'}),
            'instructions_for_use': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Specific instructions for use'}),
            'storage_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How should the medicine be stored?'}),
            'shelf_life': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12 months, 2 years'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2 tablets twice a day, 5ml every 8 hours'}),
            
            # Skills
            'traditional_medicine_skills': forms.Select(attrs={'class': 'form-select'}),
            'skills_acquired_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Provide details on how you acquired these skills'}),
            
            # Appearance
            'net_weight_volume': forms.TextInput(attrs={'class': 'form-control'}),
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
            'route_of_administration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Oral, External, Inhale...'}),
            
            # Sources
            'local_harvest_season': forms.TextInput(attrs={'class': 'form-control'}),
            'local_harvested_part': forms.TextInput(attrs={'class': 'form-control'}),
            'local_cultivated_or_wild': forms.Select(attrs={'class': 'form-select'}),
            'local_abundance': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_countries': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_plant_part': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_raw_state': forms.TextInput(attrs={'class': 'form-control'}),
            'imported_abundance': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Manufacturing Info
            'harvesting_method': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe how raw materials are harvested'}),
            'drying_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the drying process'}),
            'drying_area': forms.TextInput(attrs={'class': 'form-control'}),
            'drying_equipment': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturing_location_type': forms.Select(attrs={'class': 'form-select'}),
            'manufacturing_area_size': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturing_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide step-by-step manufacturing procedures'}),
            'equipment_used': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List all equipment used in production'}),
            'manufacturing_area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where is the medicine manufactured?'}),
            'packaging_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe how the final product is packaged'}),
            'quality_control_procedures': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Quality control procedures'}),
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
            'sample_label': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
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

