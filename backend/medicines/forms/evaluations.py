from django import forms
from medicines.models import MedicineEvaluation

class PreliminaryEvaluationForm(forms.ModelForm):
    sections_to_revise = forms.MultipleChoiceField(
        choices=[
            ('DOCUMENTS', 'Documents & Attachments'),
        ],
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Sections to Revise (Check if applying conditions)"
    )
    
    class Meta:
        model = MedicineEvaluation
        fields = [
            'documents_complete', 'documents_remarks',
            'sections_to_revise', 'overall_comments'
        ]
        widgets = {
            'documents_complete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'documents_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on Documents...'}),
            'overall_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Overall comments for the applicant... (Visible if Conditions Applied or Rejected)'}),
        }

class ScientificEvaluationForm(forms.ModelForm):
    sections_to_revise = forms.MultipleChoiceField(
        choices=[
            ('BASIC_DETAILS', 'Basic Medicine Details'),
            ('INGREDIENTS', 'Formula & Ingredients'),
            ('MANUFACTURING', 'Manufacturing & Packaging'),
        ],
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Sections to Revise (Check if applying conditions)"
    )

    class Meta:
        model = MedicineEvaluation
        fields = [
            'quality_check', 'quality_remarks',
            'safety_check', 'safety_remarks',
            'efficacy_check', 'efficacy_remarks',
            'validity_of_tests', 'validity_remarks',
            'label_inspection', 'label_remarks',
            'gmp_inspection_check', 'gmp_inspection_remarks',
            'sections_to_revise', 'overall_comments'
        ]
        widgets = {
            'quality_check': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'quality_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on Quality...'}),
            'safety_check': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'safety_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on Safety...'}),
            'efficacy_check': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'efficacy_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on Efficacy...'}),
            'validity_of_tests': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validity_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on Validity of Tests...'}),
            'label_inspection': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'label_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on Label...'}),
            'gmp_inspection_check': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gmp_inspection_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on GMP Inspection...'}),
            'overall_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Overall comments for the applicant... (Visible if Conditions Applied or Rejected)'}),
        }

