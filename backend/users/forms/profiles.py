from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.forms import UserCreationForm
from users.models import CustomUser, Role, UserProfile, CompanyProfile

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

class PractitionerDetailForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'readonly': 'readonly', 'class': 'form-control bg-light text-muted fw-bold', 'placeholder': 'Enter email address'})
    )
    phone_number = forms.CharField(
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number (e.g. 0789653278)'}),
        help_text="Exactly 10 digits starting with 0."
    )

    COUNTRY_CHOICES = [
        ('Tanzania', 'Tanzania'),
        ('Kenya', 'Kenya'),
        ('Uganda', 'Uganda'),
        ('Rwanda', 'Rwanda'),
        ('Burundi', 'Burundi'),
        ('Other', 'Other'),
    ]

    REGION_CHOICES = [
        ('', 'Select region'),
        ('Dar es Salaam', 'Dar es Salaam'),
        ('Arusha', 'Arusha'),
        ('Dodoma', 'Dodoma'),
        ('Mwanza', 'Mwanza'),
        ('Kilimanjaro', 'Kilimanjaro'),
        ('Morogoro', 'Morogoro'),
        ('Tanga', 'Tanga'),
        ('Mbeya', 'Mbeya'),
        ('Pwani', 'Pwani'),
        ('Tabora', 'Tabora'),
        ('Kagera', 'Kagera'),
        ('Kigoma', 'Kigoma'),
        ('Mara', 'Mara'),
        ('Manyara', 'Manyara'),
        ('Iringa', 'Iringa'),
        ('Ruvuma', 'Ruvuma'),
        ('Shinyanga', 'Shinyanga'),
        ('Singida', 'Singida'),
        ('Songwe', 'Songwe'),
        ('Lindi', 'Lindi'),
        ('Mtwara', 'Mtwara'),
        ('Katavi', 'Katavi'),
        ('Geita', 'Geita'),
        ('Njombe', 'Njombe'),
        ('Simiyu', 'Simiyu'),
        ('Zanzibar North', 'Zanzibar North'),
        ('Zanzibar South', 'Zanzibar South'),
        ('Zanzibar West', 'Zanzibar West'),
        ('Pemba North', 'Pemba North'),
        ('Pemba South', 'Pemba South'),
        ('Other', 'Other'),
    ]

    DISTRICT_CHOICES = [
        ('', 'Select district'),
        ('Ilala', 'Ilala'),
        ('Kinondoni', 'Kinondoni'),
        ('Temeke', 'Temeke'),
        ('Ubungo', 'Ubungo'),
        ('Kigamboni', 'Kigamboni'),
        ('Arusha Urban', 'Arusha Urban'),
        ('Arumeru', 'Arumeru'),
        ('Dodoma Urban', 'Dodoma Urban'),
        ('Nyamagana', 'Nyamagana'),
        ('Ilemela', 'Ilemela'),
        ('Moshi Urban', 'Moshi Urban'),
        ('Morogoro Urban', 'Morogoro Urban'),
        ('Tanga Urban', 'Tanga Urban'),
        ('Mbeya Urban', 'Mbeya Urban'),
        ('Other', 'Other'),
    ]

    country = forms.ChoiceField(choices=COUNTRY_CHOICES, initial='Tanzania', widget=forms.Select(attrs={'class': 'form-select'}))
    region = forms.CharField(required=False, widget=forms.Select(choices=REGION_CHOICES, attrs={'class': 'form-select'}))
    district = forms.CharField(required=False, widget=forms.Select(choices=DISTRICT_CHOICES, attrs={'class': 'form-select'}))

    class Meta:
        model = UserProfile
        fields = (
            'full_name', 'first_name', 'middle_name', 'last_name', 'surname', 'other_names', 'sex', 'age', 'date_of_birth', 'education_level',
            'nida_number', 'tin', 'country', 'region', 'district', 'ward', 'village_street',
            'residency_duration', 'postal_address', 'address', 'landline_phone', 'alternative_contact', 'fax'
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter middle name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter surname'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter other names'}),
            'sex': forms.RadioSelect(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter age'}),
            'education_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter education level'}),
            'nida_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYYMMDD-XXXXX-XXXXX-XX (e.g. 19501007-11101-00001-26)'}),
            'tin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXX-XXX-XXX (e.g. 123-456-909)'}),
            'ward': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ward'}),
            'village_street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter street or village'}),
            'residency_duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5 years'}),
            'postal_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'P.O. Box 1234, Dar es Salaam'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter full physical address'}),
            'alternative_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter alternative phone number'}),
            'landline_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter landline phone number'}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter fax number'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populate email and phone_number if user has it
        target_user = self.user or (self.instance.user if self.instance and hasattr(self.instance, 'user') else None)
        if target_user:
            self.fields['email'].initial = target_user.email
            if target_user.phone_number:
                self.fields['phone_number'].initial = target_user.phone_number
            
        for field_name, field in self.fields.items():
            if field.required:
                label = field.label or field_name.replace("_", " ").capitalize()
                field.label = mark_safe(f'<span class="text-danger">*</span> {label}')

    def clean_tin(self):
        tin = self.cleaned_data.get('tin')
        if tin:
            tin = tin.replace('-', '').replace(' ', '')
        return tin
        
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = phone.replace('-', '').replace(' ', '')
        return phone
        
    def save(self, commit=True):
        profile = super().save(commit=False)
        phone = self.cleaned_data.get('phone_number')
        
        # Auto compute full_name if first/middle/last or surname/other_names provided
        first = self.cleaned_data.get('first_name')
        middle = self.cleaned_data.get('middle_name')
        last = self.cleaned_data.get('last_name')
        surname = self.cleaned_data.get('surname')
        other_names = self.cleaned_data.get('other_names')
        
        if first or last:
            profile.full_name = f"{first or ''} {middle or ''} {last or ''}".replace('  ', ' ').strip()
        elif surname or other_names:
            profile.full_name = f"{surname or ''} {other_names or ''}".strip()
            
        if self.user:
            profile.user = self.user
        if profile.user:
            profile.user.phone_number = phone
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile

class CompanyDetailForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'readonly': 'readonly', 'class': 'form-control bg-light text-muted fw-bold', 'placeholder': 'Enter email address'})
    )
    phone_number = forms.CharField(
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number (e.g. 0789653278)'}),
        help_text="Exactly 10 digits starting with 0."
    )

    COUNTRY_CHOICES = PractitionerDetailForm.COUNTRY_CHOICES
    REGION_CHOICES = PractitionerDetailForm.REGION_CHOICES
    DISTRICT_CHOICES = PractitionerDetailForm.DISTRICT_CHOICES

    country = forms.ChoiceField(choices=COUNTRY_CHOICES, initial='Tanzania', widget=forms.Select(attrs={'class': 'form-select'}))
    region = forms.CharField(required=False, widget=forms.Select(choices=REGION_CHOICES, attrs={'class': 'form-select'}))
    district = forms.CharField(required=False, widget=forms.Select(choices=DISTRICT_CHOICES, attrs={'class': 'form-select'}))

    class Meta:
        model = CompanyProfile
        fields = (
            'company_name', 'brela_number', 'tin', 'country', 'region', 'district', 'ward',
            'village_street', 'postal_address', 'physical_address', 'landline_phone', 'alternative_contact', 'fax'
        )
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter company name'}),
            'brela_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter BRELA registration number'}),
            'tin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXX-XXX-XXX (e.g. 123-456-909)'}),
            'ward': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ward'}),
            'village_street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter street or village'}),
            'postal_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'P.O. Box 1234, Dar es Salaam'}),
            'physical_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter physical address'}),
            'alternative_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter alternative phone number'}),
            'landline_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter landline phone number'}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter fax number'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populate email and phone_number if user has it
        target_user = self.user or (self.instance.user if self.instance and hasattr(self.instance, 'user') else None)
        if target_user:
            self.fields['email'].initial = target_user.email
            if target_user.phone_number:
                self.fields['phone_number'].initial = target_user.phone_number
            
        for field_name, field in self.fields.items():
            if field.required:
                label = field.label or field_name.replace("_", " ").capitalize()
                field.label = mark_safe(f'<span class="text-danger">*</span> {label}')

    def clean_tin(self):
        tin = self.cleaned_data.get('tin')
        if tin:
            tin = tin.replace('-', '').replace(' ', '')
        return tin

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = phone.replace('-', '').replace(' ', '')
        return phone
        
    def save(self, commit=True):
        profile = super().save(commit=False)
        phone = self.cleaned_data.get('phone_number')
        if self.user:
            profile.user = self.user
        if profile.user:
            profile.user.phone_number = phone
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile

class PractitionerDocumentForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('nida_copy', 'passport_photo', 'tahpc_certificate', 'tin_certificate')
        widgets = {
            'nida_copy': forms.FileInput(attrs={'class': 'form-control'}),
            'passport_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'tahpc_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'tin_certificate': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nida_copy'].required = True

class CompanyDocumentForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = (
            'brela_certificate', 'tin_certificate', 'business_license', 
            'tahpc_certificate', 'representative_nida', 'representative_id_image'
        )
        widgets = {
            'brela_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'tin_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'business_license': forms.FileInput(attrs={'class': 'form-control'}),
            'tahpc_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'representative_nida': forms.FileInput(attrs={'class': 'form-control'}),
            'representative_id_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['brela_certificate'].required = True
        self.fields['tin_certificate'].required = True
        self.fields['business_license'].required = True
