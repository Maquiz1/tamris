from django import forms
from django.db.models import Q

from medicines.models import MedicineApplication, SystemSettings
from medicines import services
from users.models import CustomUser, Organization, ApplicantIdentity, Individual
from core.utils.fees import FEE_TYPES

INPUT = {'class': 'form-control'}
SELECT = {'class': 'form-select'}


class LegacyApplicantForm(forms.Form):
    """An applicant (person or company) known from paper records."""
    APPLICANT_TYPES = [('Individual', 'Individual'), ('Organization', 'Company / Institution')]
    ID_TYPES = [('NIDA (National ID)', 'NIDA (Tanzanian)'), ('Passport (Hati ya kusafiria)', 'Passport (foreigner)')]

    applicant_type = forms.ChoiceField(choices=APPLICANT_TYPES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs=INPUT), help_text='Used to invite the applicant to TAMRIS.')
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))

    # Individual
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))
    middle_name = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))
    identity_type = forms.ChoiceField(required=False, choices=ID_TYPES, widget=forms.Select(attrs=SELECT))
    identity_number = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))

    # Company
    organization_name = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))
    registration_number = forms.CharField(required=False, label='BRELA registration number', widget=forms.TextInput(attrs=INPUT))
    representative_name = forms.CharField(required=False, label='Responsible person', widget=forms.TextInput(attrs=INPUT))

    tin = forms.CharField(required=False, label='TIN', widget=forms.TextInput(attrs=INPUT))
    region = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))
    district = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))
    postal_address = forms.CharField(required=False, widget=forms.TextInput(attrs=INPUT))

    # Scans of paper documents
    nida_copy = forms.FileField(required=False, label='NIDA / passport copy')
    tahpc_certificate = forms.FileField(required=False, label='TAHPC certificate')
    brela_certificate = forms.FileField(required=False, label='BRELA certificate')
    tin_certificate = forms.FileField(required=False, label='TIN certificate')
    business_license = forms.FileField(required=False, label='Business licence')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists. Pick that applicant on the medicine form instead.')
        return email

    def clean_tin(self):
        return (self.cleaned_data.get('tin') or '').replace('-', '').strip() or None

    def clean(self):
        data = super().clean()
        if data.get('applicant_type') == 'Individual':
            for field in ('first_name', 'last_name', 'identity_number'):
                if not data.get(field):
                    self.add_error(field, 'Required for an individual.')
            number = data.get('identity_number')
            if number and ApplicantIdentity.objects.filter(identity_number=number).exists():
                self.add_error('identity_number', 'This ID number already belongs to an applicant in TAMRIS.')
            if data.get('tin') and Individual.objects.filter(tin=data['tin']).exists():
                self.add_error('tin', 'This TIN already belongs to an applicant in TAMRIS.')
        elif data.get('applicant_type') == 'Organization':
            if not data.get('organization_name'):
                self.add_error('organization_name', 'Required for a company.')
            name = data.get('organization_name')
            if name and Organization.objects.filter(organization_name__iexact=name).exists():
                self.add_error('organization_name', 'A company with this name is already in TAMRIS.')
            reg = data.get('registration_number')
            if reg and Organization.objects.filter(registration_number=reg).exists():
                self.add_error('registration_number', 'This BRELA number already belongs to a company in TAMRIS.')
            if data.get('tin') and Organization.objects.filter(tin=data['tin']).exists():
                self.add_error('tin', 'This TIN already belongs to a company in TAMRIS.')
        return data


def applicant_choices_queryset():
    return CustomUser.objects.filter(
        Q(role__name__in=['Individual Applicant', 'Company Applicant']) | Q(is_legacy=True),
        is_active=True,
    ).distinct().order_by('email')


class ApplicantChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.display_name} <{obj.email}>"


class LegacyMedicineForm(forms.ModelForm):
    """A medicine listed, registered or rejected on paper before TAMRIS."""
    OUTCOMES = [('CERTIFIED', 'Listed / registered (has a certificate)'), ('REJECTED', 'Rejected')]

    applicant = ApplicantChoiceField(queryset=CustomUser.objects.none(), widget=forms.Select(attrs=SELECT))
    outcome = forms.ChoiceField(choices=OUTCOMES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))

    class Meta:
        model = MedicineApplication
        fields = [
            'applicant', 'application_type', 'medicine_name', 'dosage_form', 'dosage_form_other', 'medicine_color',
            'active_ingredients', 'indications', 'shelf_life', 'shelf_life_duration_type',
            'net_weight_volume', 'net_weight_volume_unit', 'packaging_size', 'packaging_color', 'lid_color',
            'storage_conditions', 'storage_conditions_other', 'manufacturer_name', 'manufacturer_address',
            'certificate_number', 'certificate_issued_on', 'certificate_expires_on',
            'legacy_certificate_scan', 'legacy_application_scan', 'rejection_reason',
        ]
        widgets = {
            'application_type': forms.Select(attrs=SELECT),
            'medicine_name': forms.TextInput(attrs=INPUT),
            'dosage_form': forms.Select(attrs=SELECT),
            'dosage_form_other': forms.TextInput(attrs=INPUT),
            'medicine_color': forms.TextInput(attrs=INPUT),
            'active_ingredients': forms.Textarea(attrs={**INPUT, 'rows': 2}),
            'indications': forms.Textarea(attrs={**INPUT, 'rows': 2}),
            'shelf_life': forms.NumberInput(attrs=INPUT),
            'shelf_life_duration_type': forms.Select(attrs=SELECT),
            'net_weight_volume': forms.NumberInput(attrs={**INPUT, 'step': '0.01'}),
            'net_weight_volume_unit': forms.Select(attrs=SELECT),
            'packaging_size': forms.TextInput(attrs=INPUT),
            'packaging_color': forms.TextInput(attrs=INPUT),
            'lid_color': forms.TextInput(attrs=INPUT),
            'storage_conditions': forms.Select(attrs=SELECT),
            'storage_conditions_other': forms.TextInput(attrs=INPUT),
            'manufacturer_name': forms.TextInput(attrs=INPUT),
            'manufacturer_address': forms.Textarea(attrs={**INPUT, 'rows': 2}),
            'certificate_number': forms.TextInput(attrs={**INPUT, 'placeholder': 'e.g. TZ26TM0187'}),
            'certificate_issued_on': forms.DateInput(attrs={**INPUT, 'type': 'date'}, format='%Y-%m-%d'),
            'certificate_expires_on': forms.DateInput(attrs={**INPUT, 'type': 'date'}, format='%Y-%m-%d'),
            'legacy_certificate_scan': forms.FileInput(attrs={**INPUT, 'accept': 'image/*,.pdf'}),
            'legacy_application_scan': forms.FileInput(attrs={**INPUT, 'accept': 'image/*,.pdf'}),
            'rejection_reason': forms.Textarea(attrs={**INPUT, 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['applicant'].queryset = applicant_choices_queryset()
        self.fields['indications'].required = False
        if self.instance and self.instance.pk:
            self.fields['outcome'].initial = 'REJECTED' if self.instance.status == 'REJECTED' else 'CERTIFIED'

    def clean_medicine_name(self):
        name = self.cleaned_data.get('medicine_name')
        clash = MedicineApplication.objects.filter(medicine_name__iexact=name)
        if self.instance and self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('A medicine with this name is already in TAMRIS.')
        return name

    def clean(self):
        data = super().clean()
        if data.get('outcome') == 'CERTIFIED':
            for field in ('certificate_number', 'certificate_issued_on', 'certificate_expires_on'):
                if not data.get(field):
                    self.add_error(field, 'Required for a listed or registered medicine.')
            if not data.get('legacy_certificate_scan') and not (self.instance and self.instance.legacy_certificate_scan):
                self.add_error('legacy_certificate_scan', 'Attach the scan of the paper certificate.')
            issued, expires = data.get('certificate_issued_on'), data.get('certificate_expires_on')
            if issued and expires and expires <= issued:
                self.add_error('certificate_expires_on', 'The expiry date must be after the issue date.')
            if data.get('certificate_number'):
                try:
                    data['certificate_number'] = services.validate_paper_certificate_number(
                        data['certificate_number'], data.get('application_type'),
                        exclude_pk=self.instance.pk if self.instance else None,
                    )
                except services.WorkflowError as e:
                    self.add_error('certificate_number', str(e))
        elif data.get('outcome') == 'REJECTED':
            if not data.get('rejection_reason'):
                self.add_error('rejection_reason', 'Give the reason the Council rejected it.')
            data['certificate_number'] = None
            data['certificate_issued_on'] = None
            data['certificate_expires_on'] = None
        return data


PAYMENT_FEE_CHOICES = [('', '— none —')] + [(c, n) for c, n in FEE_TYPES]


class LegacyPaymentForm(forms.Form):
    payment_type = forms.ChoiceField(choices=PAYMENT_FEE_CHOICES, required=False, widget=forms.Select(attrs=SELECT))
    amount = forms.DecimalField(required=False, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={**INPUT, 'placeholder': 'Leave empty if not verified'}))
    receipt_number = forms.CharField(required=False, max_length=50, widget=forms.TextInput(attrs=INPUT))


LegacyPaymentFormSet = forms.formset_factory(LegacyPaymentForm, extra=3, max_num=6)


class RegistrarDecisionForm(forms.Form):
    reason = forms.CharField(required=False, widget=forms.Textarea(attrs={**INPUT, 'rows': 3}))


DOCUMENT_CHOICES = {
    'listing': [
        ('sample_label', 'Sample medicine label'), ('statement_of_efficacy', 'Statement of efficacy'),
        ('literature_review', 'Literature review'), ('tahpc_certificate', 'TAHPC certificate'),
        ('ingredients_info_doc', 'Ingredients information'), ('medicine_photos', 'Medicine photos'),
        ('instructions_doc', 'Instructions for use'),
    ],
    'category_ii': [
        ('sample_label', 'Sample medicine label'), ('statement_of_efficacy', 'Statement of efficacy'),
        ('literature_review', 'Literature review'), ('tahpc_certificate', 'TAHPC certificate'),
        ('ingredients_info_doc', 'Ingredients information'), ('medicine_photos', 'Medicine photos'),
        ('instructions_doc', 'Instructions for use'), ('manufacturing_flow_chart', 'Manufacturing flow chart'),
        ('scientific_name_report', 'Scientific name report'), ('heavy_metals_report', 'Heavy metals report'),
        ('pesticides_report', 'Pesticides report'), ('toxic_chemicals_report', 'Toxic chemicals report'),
        ('conventional_drugs_report', 'Conventional drugs report'), ('foreign_matter_report', 'Foreign matter report'),
        ('microbes_report', 'Microbes report'), ('aflatoxin_report', 'Aflatoxin report'),
        ('toxicity_report', 'Toxicity report'), ('stability_report', 'Stability report'),
        ('moisture_analysis_report', 'Moisture analysis'), ('ph_analysis_report', 'pH analysis'),
        ('uniformity_test_report', 'Uniformity tests'), ('dissolution_test_report', 'Dissolution tests'),
        ('clinical_observation_report', 'Clinical observation reports'),
    ],
    'individual': [
        ('nida_copy', 'NIDA copy'), ('passport_photo', 'Passport-size photo'), ('tahpc_certificate', 'TAHPC certificate'),
        ('tin_certificate', 'TIN certificate'), ('passport_document', 'Passport'),
    ],
    'company': [
        ('brela_certificate', 'BRELA certificate'), ('tin_certificate', 'TIN certificate'),
        ('business_license', 'Business licence'), ('tahpc_certificate', 'TAHPC certificate'),
        ('representative_nida', 'Representative NIDA'), ('representative_id_image', 'Representative ID'),
    ],
}


class SystemSettingsForm(forms.ModelForm):
    mandatory_listing_documents = forms.MultipleChoiceField(required=False, choices=DOCUMENT_CHOICES['listing'], widget=forms.CheckboxSelectMultiple)
    mandatory_category_ii_documents = forms.MultipleChoiceField(required=False, choices=DOCUMENT_CHOICES['category_ii'], widget=forms.CheckboxSelectMultiple)
    mandatory_individual_documents = forms.MultipleChoiceField(required=False, choices=DOCUMENT_CHOICES['individual'], widget=forms.CheckboxSelectMultiple)
    mandatory_company_documents = forms.MultipleChoiceField(required=False, choices=DOCUMENT_CHOICES['company'], widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = SystemSettings
        fields = [
            'category_ii_certificate_code', 'listing_certificate_code', 'certificate_digits',
            'reference_prefix', 'listing_reference_code', 'category_ii_reference_code',
            'coat_of_arms', 'council_logo', 'chairman_signature', 'registrar_signature', 'council_seal',
            'mandatory_listing_documents', 'mandatory_category_ii_documents',
            'mandatory_individual_documents', 'mandatory_company_documents',
        ]
        widgets = {
            'category_ii_certificate_code': forms.TextInput(attrs=INPUT),
            'listing_certificate_code': forms.TextInput(attrs=INPUT),
            'certificate_digits': forms.NumberInput(attrs={**INPUT, 'min': 3, 'max': 6}),
            'reference_prefix': forms.TextInput(attrs=INPUT),
            'listing_reference_code': forms.TextInput(attrs=INPUT),
            'category_ii_reference_code': forms.TextInput(attrs=INPUT),
        }

    def clean(self):
        data = super().clean()
        for field in ('category_ii_certificate_code', 'listing_certificate_code'):
            value = (data.get(field) or '').strip().upper()
            if not value.isalpha():
                self.add_error(field, 'Use letters only, e.g. TM.')
            data[field] = value
        if data.get('category_ii_certificate_code') and data.get('category_ii_certificate_code') == data.get('listing_certificate_code'):
            self.add_error('listing_certificate_code', 'Listing and Category II need different codes so their numbers never clash.')
        if data.get('listing_reference_code') and data.get('listing_reference_code') == data.get('category_ii_reference_code'):
            self.add_error('category_ii_reference_code', 'Listing and Category II need different reference codes.')
        return data


class CounterForm(forms.Form):
    """Starting point of this year's certificate counters."""
    listing_last_number = forms.IntegerField(min_value=0, label='Listing: last number already used', widget=forms.NumberInput(attrs=INPUT))
    category_ii_last_number = forms.IntegerField(min_value=0, label='Category II: last number already used', widget=forms.NumberInput(attrs=INPUT))
