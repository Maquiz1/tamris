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
        fields = ('first_name', 'middle_name', 'last_name', 'sex', 'date_of_birth', 'tin')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tin': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '11'})
        }

    def clean_tin(self):
        tin = self.cleaned_data.get('tin')
        if tin:
            return tin.replace('-', '')
        return tin

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ('organization_name', 'organization_type', 'registration_number', 'date_registered', 'tin', 'year_established')
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_type': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_registered': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tin': forms.TextInput(attrs={'class': 'form-control'}),
            'year_established': forms.NumberInput(attrs={'class': 'form-control'})
        }

    def clean_tin(self):
        tin = self.cleaned_data.get('tin')
        if tin:
            return tin.replace('-', '')
        return tin

ApplicantIdentityFormSet = inlineformset_factory(
    Applicant, ApplicantIdentity,
    fields=('identity_type', 'identity_number', 'is_primary'),
    extra=1,
    max_num=1,
    can_delete=False,
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
    fields=('country', 'region', 'district', 'ward', 'street', 'residency_duration', 'physical_address', 'postal_address'),
    extra=1,
    can_delete=True,
    widgets={
        'country': forms.Select(attrs={'class': 'form-select', 'required': 'required'}, choices=[('Tanzania', 'Tanzania')]),
        'region': forms.Select(attrs={'class': 'form-select', 'required': 'required'}, choices=[('', 'Select Region')]),
        'district': forms.Select(attrs={'class': 'form-select', 'required': 'required'}, choices=[('', 'Select District')]),
        'ward': forms.Select(attrs={'class': 'form-select', 'required': 'required'}, choices=[('', 'Select Ward')]),
        'street': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
        'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        'postal_address': forms.TextInput(attrs={'class': 'form-control'}),
        'residency_duration': forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'e.g. 5 Years'}),
    }
)

class ApplicantContactForm(forms.ModelForm):
    class Meta:
        model = ApplicantContact
        fields = ('mobile_phone', 'landline', 'fax', 'email')
        widgets = {
            'mobile_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'landline': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'})
        }

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
    fields=('first_name', 'middle_name', 'last_name', 'position', 'is_primary'),
    extra=1,
    max_num=1,
    can_delete=False,
    widgets={
        'first_name': forms.TextInput(attrs={'class': 'form-control'}),
        'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
        'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        'position': forms.TextInput(attrs={'class': 'form-control'}),
        'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'})
    }
)

# Stubs for old forms to prevent import errors in other views that haven't been updated yet
class PractitionerDetailForm(forms.Form):
    pass
class CompanyDetailForm(forms.Form):
    pass
class PractitionerDocumentForm(forms.Form):
    nida_copy = forms.FileField(required=False)
    passport_photo = forms.FileField(required=False)
    tahpc_certificate = forms.FileField(required=False)
    tin_certificate = forms.FileField(required=False)
    passport_document = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        if self.instance:
            for doc in self.instance.documents.all():
                if doc.document_type in self.fields:
                    self.fields[doc.document_type].initial = doc.file

    def clean(self):
        cleaned_data = super().clean()
        nida = cleaned_data.get('nida_copy')
        tin = cleaned_data.get('tin_certificate')
        
        # Check existing if they didn't upload a new one
        has_existing_nida = self.instance and self.instance.documents.filter(document_type='nida_copy').exists()
        has_existing_tin = self.instance and self.instance.documents.filter(document_type='tin_certificate').exists()
        
        has_nida = bool(nida) or has_existing_nida
        has_tin = bool(tin) or has_existing_tin
        
        if not (has_nida or has_tin):
            raise forms.ValidationError("You must provide either a NIDA copy or a TIN Certificate.")
            
        return cleaned_data

    def save(self):
        if not self.instance:
            return None
        for field_name, file in self.cleaned_data.items():
            if file:
                ApplicantDocument.objects.update_or_create(
                    applicant=self.instance,
                    document_type=field_name,
                    defaults={'file': file}
                )
        return self.instance

class CompanyDocumentForm(forms.Form):
    brela_certificate = forms.FileField(required=False)
    tin_certificate = forms.FileField(required=False)
    business_license = forms.FileField(required=False)
    tahpc_certificate = forms.FileField(required=False)
    representative_nida = forms.FileField(required=False)
    representative_id_image = forms.FileField(required=False)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        if self.instance:
            for doc in self.instance.documents.all():
                if doc.document_type in self.fields:
                    self.fields[doc.document_type].initial = doc.file

    def clean(self):
        cleaned_data = super().clean()
        brela = cleaned_data.get('brela_certificate')
        tin = cleaned_data.get('tin_certificate')
        business = cleaned_data.get('business_license')
        
        has_existing_brela = self.instance and self.instance.documents.filter(document_type='brela_certificate').exists()
        has_existing_tin = self.instance and self.instance.documents.filter(document_type='tin_certificate').exists()
        has_existing_business = self.instance and self.instance.documents.filter(document_type='business_license').exists()
        
        has_brela = bool(brela) or has_existing_brela
        has_tin = bool(tin) or has_existing_tin
        has_business = bool(business) or has_existing_business
        
        if not (has_brela or has_tin or has_business):
            raise forms.ValidationError("You must provide either a BRELA Certificate, TIN Certificate, or Business License.")
            
        return cleaned_data

    def save(self):
        if not self.instance:
            return None
        for field_name, file in self.cleaned_data.items():
            if file:
                ApplicantDocument.objects.update_or_create(
                    applicant=self.instance,
                    document_type=field_name,
                    defaults={'file': file}
                )
        return self.instance
class UserIdentificationFormSet(forms.Form):
    pass
