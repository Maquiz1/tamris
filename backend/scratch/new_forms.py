from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from users.models import CustomUser, Role, Applicant, Individual, Organization, ApplicantIdentity, ApplicantAddress, ApplicantContact, Education, OrganizationRepresentative, ApplicantDocument

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                label = field.label or field_name.replace("_", " ").capitalize()
                field.label = mark_safe(f'<span class="text-danger">*</span> {label}')

class RoleSelectionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = Role.objects.filter(name__in=['Individual Applicant', 'Company Applicant'])
        for field_name, field in self.fields.items():
            if field.required:
                label = field.label or field_name.replace("_", " ").capitalize()
                field.label = mark_safe(f'<span class="text-danger">*</span> {label}')

    class Meta:
        model = CustomUser
        fields = ('role',)
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'})
        }

class ApplicantTypeForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ('applicant_type',)
        widgets = {
            'applicant_type': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }

class IndividualForm(forms.ModelForm):
    class Meta:
        model = Individual
        fields = ('first_name', 'middle_name', 'last_name', 'sex', 'date_of_birth')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        }

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('organization_name', 'organization_type', 'registration_number', 'tin', 'year_established')
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_type': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'tin': forms.TextInput(attrs={'class': 'form-control'}),
            'year_established': forms.NumberInput(attrs={'class': 'form-control'})
        }

ApplicantIdentityFormSet = inlineformset_factory(
    Applicant, ApplicantIdentity,
    fields=('identity_type', 'identity_number', 'is_primary'),
    extra=1,
    can_delete=True,
    widgets={
        'identity_type': forms.Select(attrs={'class': 'form-select'}),
        'identity_number': forms.TextInput(attrs={'class': 'form-control'}),
        'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'})
    },
    help_texts={
        'identity_number': 'Formats: NIDA (20 digits), Passport (e.g., AB123456), Driver\'s License (10 digits), Voter\'s ID (e.g., T-XXXX-XXXX-XXXX)'
    }
)

ApplicantAddressFormSet = inlineformset_factory(
    Applicant, ApplicantAddress,
    fields=('country', 'region', 'district', 'ward', 'street', 'physical_address', 'postal_address'),
    extra=1,
    can_delete=True,
    widgets={
        'country': forms.TextInput(attrs={'class': 'form-control'}),
        'region': forms.TextInput(attrs={'class': 'form-control'}),
        'district': forms.TextInput(attrs={'class': 'form-control'}),
        'ward': forms.TextInput(attrs={'class': 'form-control'}),
        'street': forms.TextInput(attrs={'class': 'form-control'}),
        'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        'postal_address': forms.TextInput(attrs={'class': 'form-control'}),
    }
)

ApplicantContactFormSet = inlineformset_factory(
    Applicant, ApplicantContact,
    fields=('contact_type', 'contact_value', 'is_primary'),
    extra=1,
    can_delete=True,
    widgets={
        'contact_type': forms.Select(attrs={'class': 'form-select'}),
        'contact_value': forms.TextInput(attrs={'class': 'form-control'}),
        'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'})
    }
)

EducationFormSet = inlineformset_factory(
    Applicant, Education,
    fields=('education_level',),
    extra=1,
    can_delete=True,
    widgets={
        'education_level': forms.Select(attrs={'class': 'form-select'})
    }
)

OrganizationRepresentativeFormSet = inlineformset_factory(
    Organization, OrganizationRepresentative,
    fields=('first_name', 'middle_name', 'last_name', 'position', 'phone', 'email', 'identity_type', 'identity_number', 'is_primary'),
    extra=1,
    can_delete=True,
    widgets={
        'first_name': forms.TextInput(attrs={'class': 'form-control'}),
        'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
        'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        'position': forms.TextInput(attrs={'class': 'form-control'}),
        'phone': forms.TextInput(attrs={'class': 'form-control'}),
        'email': forms.EmailInput(attrs={'class': 'form-control'}),
        'identity_type': forms.Select(attrs={'class': 'form-select'}),
        'identity_number': forms.TextInput(attrs={'class': 'form-control'}),
        'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'})
    }
)

# Stubs for old forms to prevent import errors in other views that haven't been updated yet
class PractitionerDetailForm(forms.Form):
    pass
class CompanyDetailForm(forms.Form):
    pass
class PractitionerDocumentForm(forms.Form):
    pass
class CompanyDocumentForm(forms.Form):
    pass
class UserIdentificationFormSet(forms.Form):
    pass
