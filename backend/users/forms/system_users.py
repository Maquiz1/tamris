from django import forms
from users.models import CustomUser, Role

class StaffUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number')
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '0XXX-XXX-XXX (e.g. 0789-653-278)'}),
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)

class StaffUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'role', 'additional_roles', 'is_active')
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '0XXX-XXX-XXX (e.g. 0789-653-278)'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'additional_roles': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        staff_roles = Role.objects.exclude(name__in=['Individual Applicant', 'Company Applicant'])
        if request_user and not request_user.is_superuser:
            staff_roles = staff_roles.exclude(name='Admin')
            
        self.fields['role'].queryset = staff_roles
        self.fields['additional_roles'].queryset = staff_roles
        self.fields['role'].help_text = "Primary Role"
        self.fields['additional_roles'].help_text = "Select any additional roles for this staff member."


