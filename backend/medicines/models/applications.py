from core.utils.uploads import medicine_document_path
from django.db import models
from django.conf import settings
from core.models import TimeStampedModel

class MedicineApplication(TimeStampedModel):
    APPLICATION_TYPES = [
        ('LISTING', 'Listing of Traditional Medicines'),
        ('CATEGORY_II', 'Registration of Category II Traditional Medicines'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING_APPLICATION_FEE', 'Pending: Ada ya maombi (Application fee)'),
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted / Pending Review'),
        ('PENDING_EVALUATION_FEE', 'Pending: Ada ya tathmini (Evaluation fee)'),
        ('UNDER_REVIEW', 'Under Review'),
        ('PRELIMINARY_APPROVED', 'Preliminary Approved / Pending Scientific'),
        ('PENDING_INSPECTION_FEE', 'Pending: Ada ya ukaguzi wa uzalishaji (Manufacturing inspection fee)'),
        ('READY_FOR_INSPECTION', 'Ready for Inspection'),
        ('INSPECTION_COMPLETED', 'Inspection Completed / Pending Scientific'),
        ('PENDING_LISTING_FEE', 'Pending: Ada ya uorodheshaji (Listing fee)'),
        ('PENDING_REGISTRATION_FEE', 'Pending: Ada ya usajili (Registration fee)'),
        ('PENDING_FINAL_APPROVAL', 'Pending Final Approval'),
        ('PROVISIONAL_REGISTRATION', 'Provisional Registration'),
        ('FULL_REGISTRATION', 'Full Registration'),
        ('CONDITIONS_APPLIED', 'Conditions for Improvement'),
        ('REJECTED', 'Rejected'),
    ]

    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medicine_applications')
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES)
    
    # Applicant Skills (Ujuzi katika Tiba Asili / Miti Dawa)
    SKILL_CHOICES = [
        ('MAFUNZO', 'Mafunzo rasmi'),
        ('KURITHI', 'Kurithi'),
        ('MENGINEYO', 'Mengineyo')
    ]
    traditional_medicine_skills = models.CharField(max_length=20, choices=SKILL_CHOICES, blank=True, null=True, verbose_name="Ulipataje ujuzi katika tiba asili?")
    
    DURATION_CHOICES = [
        ('YEARS', 'Miaka (Years)'),
        ('MONTHS', 'Miezi (Months)'),
        ('WEEKS', 'Majuma (Weeks)'),
        ('DAYS', 'Siku (Days)'),
    ]

    # 1.7.1 Mafunzo rasmi
    training_institution = models.CharField(max_length=255, blank=True, null=True, verbose_name="Taja Taasisi ya Mafunzo / Mganga wa Tiba Asili")
    training_duration = models.IntegerField(blank=True, null=True, verbose_name="Muda wa mafunzo")
    training_duration_type = models.CharField(max_length=20, choices=DURATION_CHOICES, blank=True, null=True, verbose_name="Aina ya muda")
    
    # 1.7.2 Kurithi
    inherited_from = models.CharField(max_length=255, blank=True, null=True, verbose_name="Taja jina la fundi / mtu uliyemrithi")
    inherited_duration = models.IntegerField(blank=True, null=True, verbose_name="Muda uliojifunza")
    inherited_duration_type = models.CharField(max_length=20, choices=DURATION_CHOICES, blank=True, null=True, verbose_name="Aina ya muda")
    
    # 1.7.3 Mengineyo
    traditional_medicine_skills_other = models.TextField(blank=True, null=True, verbose_name="Mengineyo; eleza")

    DOSAGE_FORM_CHOICES = [
        ('UNGA', 'Unga'),
        ('KIMIMINIKA', 'Kimiminika'),
        ('KIDONGE', 'Kidonge'),
        ('CAPSULE', 'Capsule'),
        ('NYINGINE', 'Nyingine'),
    ]

    # Basic Medicine Details
    medicine_name = models.CharField(max_length=255, verbose_name="Medicine Name (Jina la dawa)")
    dosage_form = models.CharField(max_length=100, choices=DOSAGE_FORM_CHOICES, verbose_name="Hali ya dawa (Dosage form)")
    dosage_form_other = models.CharField(max_length=100, blank=True, null=True, verbose_name="Taja Hali ya dawa")
    empty_packaging_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Ujazo wa kifungashio kabla ya kuweka dawa")
    net_weight_volume = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Kiasi (Net Weight/Net Volume)")
    
    UNIT_CHOICES = [('g', 'g'), ('mL', 'mL')]
    net_weight_volume_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, blank=True, null=True, verbose_name="Kipimo")
    
    # Appearance & Packaging
    medicine_color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rangi ya dawa")
    medicine_smell = models.CharField(max_length=100, blank=True, null=True, verbose_name="Harufu ya dawa")
    medicine_taste = models.CharField(max_length=100, blank=True, null=True, verbose_name="Radha ya dawa")
    medicine_texture = models.CharField(max_length=100, blank=True, null=True, verbose_name="Umbile la dawa (texture)")
    packaging_size = models.CharField(max_length=100, blank=True, null=True, verbose_name="Saizi ya Kifungashio")
    packaging_color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rangi ya kifungashio")
    lid_color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rangi ya kifuniko")
    other_appearance_instructions = models.TextField(blank=True, null=True, verbose_name="Maelekezo mengine")
    
    # Ingredients Information
    ingredients_table = models.TextField(blank=True, null=True, verbose_name="Mchanganyiko wa dawa (Ingredients Table)")
    active_ingredients = models.TextField(blank=True, null=True, verbose_name="Viambato vikuu (Active ingredients)")
    excipients = models.TextField(blank=True, null=True, verbose_name="Viambato vidogo (Excipients)")
    ingredients = models.TextField(blank=True, null=True, verbose_name="Medicine ingredients information (Taarifa za viambato vya dawa)", help_text="List of raw materials or herbs used")
    
    # Usage and Safety Details
    ROUTE_CHOICES = [
        ('KUPAKA', 'Kupaka'),
        ('KUNYWA', 'Kunywa'),
        ('KUVUTA', 'Kuvuta'),
        ('KUFUKIZA', 'Kufukiza'),
        ('KUSUKUTUA', 'Kusukutua'),
        ('NYINGINE', 'Njia nyingine'),
    ]
    route_of_administration = models.CharField(max_length=50, choices=ROUTE_CHOICES, blank=True, null=True, verbose_name="Namna ya utoaji wa dawa (Route of administration)")
    route_of_administration_other = models.CharField(max_length=255, blank=True, null=True, verbose_name="Njia nyingine")
    
    indications = models.TextField(help_text="What is this medicine used to treat?")
    directions_for_use = models.TextField(verbose_name="Directions for use (Namna ya matumizi)", default="")
    
    known_side_effects = models.BooleanField(default=False, verbose_name="Je, dawa ina madhara yanayojulikana?")
    possible_side_effects = models.TextField(verbose_name="Possible side effects (Madhara yanayoweza kutokea)", blank=True, null=True, default="")
    
    precautions = models.TextField(verbose_name="Precautions (Tahadhari)", default="")
    instructions_for_use = models.TextField(verbose_name="Instructions for use (Maelekezo ya matumizi)", blank=True, null=True, default="")
    
    STORAGE_CHOICES = [
        ('JOTO_LA_KAWAIDA', 'Joto la kawaida (Room Temperature)'),
        ('MAZINGIRA_MAALUM', 'Mazingira maalum'),
    ]
    storage_conditions = models.CharField(max_length=50, choices=STORAGE_CHOICES, verbose_name="Storage conditions (Masharti ya utunzaji)", default="JOTO_LA_KAWAIDA")
    storage_conditions_other = models.TextField(blank=True, null=True, verbose_name="Iwapo mazingira maalum, elezea:")
    
    shelf_life = models.IntegerField(blank=True, null=True, verbose_name="Muda wa matumizi wa dawa (Shelf life)")
    shelf_life_duration_type = models.CharField(max_length=20, choices=DURATION_CHOICES, blank=True, null=True, verbose_name="Aina ya muda (Shelf life)")
    dosage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Kipimo cha matumizi (Dosage)")
    
    # Raw Material Sources (Vyanzo vya dawa ghafi)
    CULTIVATION_CHOICES = [('INALIMWA', 'Inalimwa (Cultivated)'), ('ASILI', 'Za Asili (Wild)')]
    SEASON_CHOICES = [
        ('KIANGAZI', 'Kiangazi'),
        ('MASIKA', 'Masika'),
        ('VULI', 'Vuli'),
        ('KIPUPWE', 'Kipupwe'),
    ]
    local_harvest_season = models.CharField(max_length=50, choices=SEASON_CHOICES, blank=True, null=True, verbose_name="Msimu wa kuvuna (Local)")
    
    PLANT_PART_CHOICES = [
        ('MAJANI', 'Majani'),
        ('MIZIZI', 'Mizizi'),
        ('MAGOME', 'Magome'),
        ('MATUNDA', 'Matunda'),
        ('MAUA', 'Maua'),
        ('UTOMVU', 'Utomvu'),
        ('MENGINEYO', 'Mengineyo'),
    ]
    local_harvested_part = models.CharField(max_length=50, choices=PLANT_PART_CHOICES, blank=True, null=True, verbose_name="Sehemu inayovunwa (Local)")
    local_harvested_part_other = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sehemu nyingine")
    
    local_cultivated_or_wild = models.CharField(max_length=20, choices=CULTIVATION_CHOICES, blank=True, null=True)
    
    ABUNDANCE_CHOICES = [
        ('KUBWA_SANA', 'Upatikanaji mkubwa sana'),
        ('KUBWA', 'Upatikanaji mkubwa'),
        ('KAWAIDA', 'Upatikanaji wa kawaida'),
        ('MDOGO', 'Upatikanaji mdogo'),
        ('MDOGO_SANA', 'Upatikanaji mdogo sana'),
    ]
    local_abundance = models.CharField(max_length=50, choices=ABUNDANCE_CHOICES, blank=True, null=True, verbose_name="Hali ya upatikanaji (Local)")
    
    foreign_source_countries = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nchi zinakotoka (Countries of origin)")
    foreign_harvest_season = models.CharField(max_length=50, choices=SEASON_CHOICES, blank=True, null=True, verbose_name="Msimu wa kuvuna (Foreign)")
    foreign_harvested_part = models.CharField(max_length=50, choices=PLANT_PART_CHOICES, blank=True, null=True, verbose_name="Sehemu inayovunwa (Foreign)")
    foreign_harvested_part_other = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sehemu nyingine (Foreign)")
    foreign_cultivated_or_wild = models.CharField(max_length=20, choices=CULTIVATION_CHOICES, blank=True, null=True)
    foreign_abundance = models.CharField(max_length=50, choices=ABUNDANCE_CHOICES, blank=True, null=True, verbose_name="Hali ya upatikanaji (Foreign)")

    # Manufacturing Information (Hatua ya 3)
    harvesting_method = models.TextField(verbose_name="Method of harvesting raw materials (Namna ya uvunaji wa malighafi)", blank=True, null=True)
    does_dry_raw_materials = models.BooleanField(default=False, verbose_name="Je, una kausha dawa ghafi?")
    drying_area = models.CharField(max_length=255, blank=True, null=True, verbose_name="Sehemu unayokaushia")
    drying_equipment = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vifaa vya kukaushia")
    
    LOCATION_CHOICES = [('NDANI_YA_NYUMBA', 'Ndani ya nyumba ya kuishi'), ('LIMEJITENGA', 'Limejitenga na nyumba')]
    manufacturing_location_type = models.CharField(max_length=20, choices=LOCATION_CHOICES, blank=True, null=True)
    manufacturing_area_size = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Saizi ya eneo/jengo")
    manufacturing_procedures = models.TextField(verbose_name="Manufacturing procedures (Hatua za utengenezaji)", blank=True, null=True)
    equipment_used = models.TextField(verbose_name="Equipment used (Vifaa vinavyotumika)", blank=True, null=True)
    manufacturing_area = models.CharField(max_length=255, verbose_name="Manufacturing area (Eneo la uzalishaji)", blank=True, null=True)
    packaging_procedures = models.TextField(verbose_name="Packaging procedures (Namna ya ufungashaji)", blank=True, null=True)
    quality_control_procedures = models.TextField(verbose_name="Taratibu za udhibiti wa ubora (Quality control procedures)", blank=True, null=True)
    storage_environment = models.TextField(verbose_name="Mazingira ya utunzaji dawa iliyokwisha tengenezwa", blank=True, null=True)
    in_process_control_procedures = models.TextField(verbose_name="Hatua za udhibiti wakati wa uzalishaji (In-process control procedures)", blank=True, null=True)
    manufacturing_flow_chart = models.FileField(upload_to=medicine_document_path, verbose_name="Mchoro wa hatua za uzalishaji (Manufacturing flow chart)", blank=True, null=True)
    
    # Attachments (Hatua ya 4)
    # Note: "Sampuli tatu za dawa" is physical
    # sample_label is now handled by MedicineLabelAttachment model
    statement_of_efficacy = models.FileField(upload_to=medicine_document_path, verbose_name="Statement of efficacy (Taarifa ya ufanisi wa dawa)", blank=True, null=True)
    literature_review = models.FileField(upload_to=medicine_document_path, verbose_name="Literature review on efficacy (Mapitio ya maandiko kuhusu ufanisi)", blank=True, null=True)
    tahpc_certificate = models.FileField(upload_to=medicine_document_path, verbose_name="TAHPC practitioner certificate (Cheti cha mganga kutoka TAHPC)", blank=True, null=True)
    ingredients_info_doc = models.FileField(upload_to=medicine_document_path, verbose_name="Ingredients information doc (Taarifa za viambato)", blank=True, null=True)
    medicine_photos = models.FileField(upload_to=medicine_document_path, verbose_name="Medicine photos (Picha za dawa)", blank=True, null=True)
    instructions_doc = models.FileField(upload_to=medicine_document_path, verbose_name="Instructions for use doc (Maelekezo ya matumizi ya dawa)", blank=True, null=True)

    # Category II Specific Attachments
    scientific_name_report = models.FileField(upload_to=medicine_document_path, verbose_name="Scientific name report (Jina la kitaalam)", blank=True, null=True)
    heavy_metals_report = models.FileField(upload_to=medicine_document_path, verbose_name="Heavy metals report (Madini tembo)", blank=True, null=True)
    pesticides_report = models.FileField(upload_to=medicine_document_path, verbose_name="Pesticides report (Viuwatilifu)", blank=True, null=True)
    toxic_chemicals_report = models.FileField(upload_to=medicine_document_path, verbose_name="Toxic chemicals report (Kemikali zenye madhara)", blank=True, null=True)
    conventional_drugs_report = models.FileField(upload_to=medicine_document_path, verbose_name="Conventional drugs report (Kemikali dawa kisasa)", blank=True, null=True)
    foreign_matter_report = models.FileField(upload_to=medicine_document_path, verbose_name="Foreign matter report", blank=True, null=True)
    microbes_report = models.FileField(upload_to=medicine_document_path, verbose_name="Microbes report (Vimelea/bacteria)", blank=True, null=True)
    aflatoxin_report = models.FileField(upload_to=medicine_document_path, verbose_name="Aflatoxin report (Sumu kuvu)", blank=True, null=True)
    toxicity_report = models.FileField(upload_to=medicine_document_path, verbose_name="Toxicity results (Matokeo ya sumu)", blank=True, null=True)
    stability_report = models.FileField(upload_to=medicine_document_path, verbose_name="Stability study reports (Taarifa za uthabiti)", blank=True, null=True)
    moisture_analysis_report = models.FileField(upload_to=medicine_document_path, verbose_name="Moisture analysis (Uchunguzi wa unyevunyevu)", blank=True, null=True)
    ph_analysis_report = models.FileField(upload_to=medicine_document_path, verbose_name="pH analysis (Uchunguzi wa pH)", blank=True, null=True)
    uniformity_test_report = models.FileField(upload_to=medicine_document_path, verbose_name="Uniformity tests (Vipimo vya usawa)", blank=True, null=True)
    dissolution_test_report = models.FileField(upload_to=medicine_document_path, verbose_name="Dissolution tests (Vipimo vya mumunyo)", blank=True, null=True)
    clinical_observation_report = models.FileField(upload_to=medicine_document_path, verbose_name="Clinical observation reports (Ripoti za ufuatiliaji)", blank=True, null=True)
    brela_registration_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Jina la dawa lililosajiliwa na BRELA")

    # Certificate details (Hati)
    manufacturer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Name of manufacturer (Jina la mtengenezaji)")
    manufacturer_address = models.TextField(blank=True, null=True, verbose_name="Address of manufacturer (Anuani ya mtengenezaji)")

    # Status & Tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    review_remarks = models.TextField(blank=True, null=True, help_text="General feedback from the staff evaluator")
    rejection_reason = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    # Reference numbers, provisional letter and certificate
    reference_number = models.CharField(max_length=40, unique=True, blank=True, null=True, verbose_name="Application reference")
    former_reference = models.CharField(max_length=40, blank=True, null=True, help_text="Reference printed on provisional letters before reference numbers were stored")
    provisional_issued_on = models.DateField(blank=True, null=True)
    certificate_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    certificate_issued_on = models.DateField(blank=True, null=True)
    certificate_expires_on = models.DateField(blank=True, null=True)
    final_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='final_approvals')
    final_approved_at = models.DateTimeField(blank=True, null=True)
    renewal_count = models.PositiveIntegerField(default=0)
    renewal_reminders_sent = models.JSONField(default=list, blank=True, help_text="Days-before-expiry reminders already sent for the current expiry date")

    # Conditions for improvement
    conditions_return_status = models.CharField(max_length=30, blank=True, null=True, help_text="Status the application returns to when the applicant resubmits")

    # Legacy (paper) records entered by a Data Clerk
    LEGACY_VERIFICATION_CHOICES = [
        ('PENDING', 'Pending verification'),
        ('VERIFIED', 'Verified'),
        ('RETURNED', 'Returned for correction'),
    ]
    is_legacy = models.BooleanField(default=False)
    legacy_entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='legacy_entries')
    legacy_verification_status = models.CharField(max_length=20, choices=LEGACY_VERIFICATION_CHOICES, blank=True, null=True)
    legacy_verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='legacy_verifications')
    legacy_verified_at = models.DateTimeField(blank=True, null=True)
    legacy_return_reason = models.TextField(blank=True, null=True)
    legacy_certificate_scan = models.FileField(upload_to=medicine_document_path, blank=True, null=True, verbose_name="Scan of the paper certificate")
    legacy_application_scan = models.FileField(upload_to=medicine_document_path, blank=True, null=True, verbose_name="Scan of the paper application")
    is_void = models.BooleanField(default=False)
    void_reason = models.TextField(blank=True, null=True)

    PROVISIONAL_STATUSES = ['PENDING_LISTING_FEE', 'PENDING_REGISTRATION_FEE', 'PENDING_FINAL_APPROVAL', 'PROVISIONAL_REGISTRATION']

    def __str__(self):
        return f"{self.medicine_name} ({self.get_application_type_display()}) - {self.applicant.email}"

    @property
    def registration_number(self):
        """The stored certificate number. Kept under this name for existing templates and reports."""
        return self.certificate_number

    @property
    def is_listing(self):
        return self.application_type == 'LISTING'

    @property
    def is_visible_to_applicant(self):
        """Legacy records stay hidden until a Registrar has verified their certificate."""
        if self.is_void:
            return False
        if self.is_legacy and self.status == 'FULL_REGISTRATION':
            return self.legacy_verification_status == 'VERIFIED'
        return True

    @property
    def has_active_certificate(self):
        return (
            self.status == 'FULL_REGISTRATION'
            and bool(self.certificate_number)
            and self.is_visible_to_applicant
        )

    @property
    def is_expired(self):
        from django.utils import timezone
        return bool(self.certificate_expires_on) and self.certificate_expires_on < timezone.localdate()

    @property
    def days_to_expiry(self):
        from django.utils import timezone
        if not self.certificate_expires_on:
            return None
        return (self.certificate_expires_on - timezone.localdate()).days

    @property
    def can_renew(self):
        """Renewal opens 90 days before expiry and stays open after expiry."""
        if not self.has_active_certificate or self.days_to_expiry is None:
            return False
        if self.days_to_expiry > 90:
            return False
        return not self.payments.filter(payment_type__in=['LISTING_RENEWAL_FEE', 'CAT_II_RENEWAL_FEE'], is_verified=False).exists()

    @property
    def pending_renewal_payment(self):
        return self.payments.filter(payment_type__in=['LISTING_RENEWAL_FEE', 'CAT_II_RENEWAL_FEE'], is_verified=False).first()

    @property
    def shows_original_scan(self):
        """Legacy certificates are shown as the scanned paper original until their first renewal in the system."""
        return self.is_legacy and self.renewal_count == 0 and bool(self.legacy_certificate_scan)

    @property
    def has_provisional_letter(self):
        return self.status in self.PROVISIONAL_STATUSES or (self.status == 'FULL_REGISTRATION' and bool(self.provisional_issued_on))

    @property
    def provisional_letter_open_to_applicant(self):
        """The applicant sees the provisional letter only until the certificate is issued."""
        return self.status in self.PROVISIONAL_STATUSES and not self.is_legacy

    @property
    def display_status(self):
        if self.status == 'FULL_REGISTRATION':
            if self.is_legacy and self.legacy_verification_status != 'VERIFIED':
                return 'Pending verification'
            if self.is_expired:
                return 'Expired'
            return 'Listed' if self.is_listing else 'Registered'
        return self.get_status_display()

    # Holder details printed on letters and certificates
    @property
    def applicant_profile(self):
        return getattr(self.applicant, 'applicant_profile', None)

    @property
    def holder_name(self):
        profile = self.applicant_profile
        if profile is not None:
            if profile.applicant_type == 'Organization' and hasattr(profile, 'organization'):
                return profile.organization.organization_name
            if hasattr(profile, 'individual'):
                return profile.individual.full_name
        return self.applicant.display_name

    @property
    def holder_address(self):
        profile = self.applicant_profile
        address = profile.address_obj if profile is not None else None
        if not address:
            return ''
        parts = [address.postal_address, address.street, address.ward, address.district, address.region]
        return ', '.join(p for p in parts if p)

    @property
    def responsible_person(self):
        profile = self.applicant_profile
        if profile is not None:
            if profile.applicant_type == 'Organization' and hasattr(profile, 'organization'):
                reps = list(profile.organization.representatives.all())
                rep = next((r for r in reps if r.is_primary), reps[0] if reps else None)
                if rep:
                    return " ".join(filter(None, [rep.first_name, rep.middle_name, rep.last_name]))
                return ''
            if hasattr(profile, 'individual'):
                return profile.individual.full_name
        return self.applicant.display_name

    @property
    def shelf_life_display(self):
        if not self.shelf_life:
            return ''
        unit = self.shelf_life_duration_type
        if unit == 'YEARS':
            return f"{self.shelf_life * 12}"
        if unit in (None, '', 'MONTHS'):
            return f"{self.shelf_life}"
        return f"{self.shelf_life} {self.get_shelf_life_duration_type_display()}"

    @property
    def form_and_colour(self):
        form = self.dosage_form_other if self.dosage_form == 'NYINGINE' and self.dosage_form_other else self.get_dosage_form_display()
        return " ".join(filter(None, [self.medicine_color, form])).strip()

    @property
    def pack_description(self):
        parts = []
        if self.net_weight_volume:
            parts.append(f"{self.net_weight_volume.normalize():f} {self.net_weight_volume_unit or ''}".strip())
        if self.packaging_color or self.packaging_size:
            parts.append(" ".join(filter(None, [self.packaging_color, self.packaging_size, 'container'])))
        if self.lid_color:
            parts.append(f"fitted with a {self.lid_color} lid")
        return " ".join(parts)

    @property
    def storage_statement(self):
        if self.storage_conditions == 'MAZINGIRA_MAALUM' and self.storage_conditions_other:
            return self.storage_conditions_other
        return self.get_storage_conditions_display()

    @property
    def requires_applicant_action(self):
        if self.status in ['DRAFT', 'CONDITIONS_APPLIED']:
            return True
        if 'PENDING' in self.status and 'FEE' in self.status:
            payments = list(self.payments.all())
            if payments:
                payment = payments[-1]
                if not payment.control_number and not payment.is_verified:
                    return True
        if self.status == 'FULL_REGISTRATION':
            renewal = self.pending_renewal_payment
            if renewal and not renewal.control_number:
                return True
        return False

    class Meta:
        ordering = ['-created_at']

class MedicineLabelAttachment(models.Model):
    application = models.ForeignKey(MedicineApplication, on_delete=models.CASCADE, related_name='label_attachments')
    file = models.FileField(upload_to=medicine_document_path, verbose_name="Sample medicine label attachment")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Label for {self.application.medicine_name}"
