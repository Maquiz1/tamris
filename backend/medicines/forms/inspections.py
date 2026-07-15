from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from medicines.models import InspectionSchedule

class InspectionScheduleForm(forms.ModelForm):
    assigned_inspectors = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        help_text="Select one or more inspectors to assign to this task."
    )

    class Meta:
        model = InspectionSchedule
        fields = [
            'assigned_inspectors',
            'evaluator_remarks_for_inspectors', 'evaluator_remarks_for_applicant',
            'start_date_time', 'end_date_time',
            'check_manufacturing_area', 'check_machines',
            'check_cleanliness', 'check_medicine_storage',
            'check_quality_control'
        ]
        widgets = {
            'evaluator_remarks_for_inspectors': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional instructions/remarks for the assigned inspectors...'}),
            'evaluator_remarks_for_applicant': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes/remarks that will be sent to the applicant...'}),
            'start_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'check_manufacturing_area': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'check_machines': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'check_cleanliness': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'check_medicine_storage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'check_quality_control': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        self.fields['assigned_inspectors'].queryset = User.objects.filter(
            Q(role__name='Inspector') | Q(additional_roles__name='Inspector'),
            is_active=True
        ).distinct()

class InspectionReportForm(forms.ModelForm):
    class Meta:
        model = InspectionSchedule
        fields = [
            'manufacturing_area_remarks', 'machines_remarks',
            'cleanliness_remarks', 'medicine_storage_remarks',
            'quality_control_remarks', 'report_file', 'remarks', 'gmp_compliant'
        ]
        widgets = {
            'manufacturing_area_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on manufacturing area...'}),
            'machines_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on machines...'}),
            'cleanliness_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on cleanliness...'}),
            'medicine_storage_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on medicine storage...'}),
            'quality_control_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Remarks on quality control...'}),
            'report_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter overall inspection remarks or findings...'}),
            'gmp_compliant': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if not self.instance.check_manufacturing_area:
                self.fields.pop('manufacturing_area_remarks', None)
            if not self.instance.check_machines:
                self.fields.pop('machines_remarks', None)
            if not self.instance.check_cleanliness:
                self.fields.pop('cleanliness_remarks', None)
            if not self.instance.check_medicine_storage:
                self.fields.pop('medicine_storage_remarks', None)
            if not self.instance.check_quality_control:
                self.fields.pop('quality_control_remarks', None)
