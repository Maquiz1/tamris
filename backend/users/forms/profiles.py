from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser, Role, UserProfile, CompanyProfile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number')
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '0XXX-XXX-XXX (e.g. 0789-653-278)', 'required': True})
        }

class RoleSelectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.filter(name__in=['Individual Applicant', 'Company Applicant'])

    class Meta:
        model = CustomUser
        fields = ('role',)
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'})
        }

class PractitionerDetailForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('full_name', 'nida_number', 'tin', 'address')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'nida_number': forms.TextInput(attrs={'placeholder': 'YYYYMMDD-XXXXX-XXXX-XXX (e.g. 19810822-61218-9000-125)'}),
            'tin': forms.TextInput(attrs={'placeholder': 'XXX-XXX-XXX (e.g. 123-456-909)'})
        }

class CompanyDetailForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ('company_name', 'brela_number', 'tin', 'physical_address')
        widgets = {
            'physical_address': forms.Textarea(attrs={'rows': 2}),
            'tin': forms.TextInput(attrs={'placeholder': 'XXX-XXX-XXX (e.g. 123-456-909)'})
        }

class PractitionerDocumentForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('nida_copy', 'passport_photo', 'tahpc_certificate', 'tin_certificate')

class CompanyDocumentForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = (
            'brela_certificate', 'tin_certificate', 'business_license', 
            'tahpc_certificate', 'representative_nida', 'representative_id_image'
        )
