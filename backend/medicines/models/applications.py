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
    
    # Applicant Skills (Ujuzi katika tiba asili)
    SKILL_CHOICES = [
        ('MAFUNZO', 'Mafunzo (Training)'),
        ('KURITHI', 'Kurithi (Inherited)'),
        ('MENGINEYO', 'Mengineyo (Other)')
    ]
    traditional_medicine_skills = models.CharField(max_length=20, choices=SKILL_CHOICES, blank=True, null=True, verbose_name="Ujuzi katika tiba asili")
    skills_acquired_details = models.TextField(blank=True, null=True, verbose_name="Ulipataje ujuzi huo (How acquired)")

    # Basic Medicine Details
    medicine_name = models.CharField(max_length=255, verbose_name="Medicine Name (Jina la dawa)")
    dosage_form = models.CharField(max_length=100, help_text="e.g., Liquid, Powder, Tablet, Cream")
    net_weight_volume = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kiasi (Net Weight/Net Volume)")
    
    # Appearance & Packaging
    medicine_color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rangi ya dawa")
    medicine_smell = models.CharField(max_length=100, blank=True, null=True, verbose_name="Harufu ya dawa")
    medicine_taste = models.CharField(max_length=100, blank=True, null=True, verbose_name="Radha ya dawa")
    medicine_texture = models.CharField(max_length=100, blank=True, null=True, verbose_name="Umbile la dawa (texture)")
    packaging_size = models.CharField(max_length=100, blank=True, null=True, verbose_name="Saizi ya Kifungashio")
    packaging_color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rangi ya kifungashio")
    lid_color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Rangi ya kifuniko")
    other_appearance_instructions = models.TextField(blank=True, null=True, verbose_name="Maelekezo mengine ya muonekano")
    
    # Ingredients Information
    ingredients_table = models.TextField(blank=True, null=True, verbose_name="Mchanganyiko wa dawa (Ingredients Table)")
    active_ingredients = models.TextField(blank=True, null=True, verbose_name="Viambato vikuu (Active ingredients)")
    excipients = models.TextField(blank=True, null=True, verbose_name="Viambato vidogo (Excipients)")
    ingredients = models.TextField(verbose_name="Medicine ingredients information (Taarifa za viambato vya dawa)", help_text="List of raw materials or herbs used")
    
    # Usage and Safety Details
    route_of_administration = models.CharField(max_length=255, blank=True, null=True, verbose_name="Namna ya utoaji wa dawa (Route of administration)")
    indications = models.TextField(help_text="What is this medicine used to treat?")
    directions_for_use = models.TextField(verbose_name="Directions for use (Namna ya matumizi)", default="")
    possible_side_effects = models.TextField(verbose_name="Possible side effects (Madhara yanayoweza kutokea)", default="")
    precautions = models.TextField(verbose_name="Precautions (Tahadhari)", default="")
    instructions_for_use = models.TextField(verbose_name="Instructions for use (Maelekezo ya matumizi)", default="")
    storage_conditions = models.TextField(verbose_name="Storage conditions (Masharti ya utunzaji)", default="")
    shelf_life = models.CharField(max_length=100, blank=True, null=True, verbose_name="Muda wa matumizi wa dawa (Shelf life)")
    dosage = models.CharField(max_length=255, blank=True, null=True, verbose_name="Kipimo cha matumizi (Dosage)")
    
    # Raw Material Sources (Vyanzo vya dawa ghafi)
    CULTIVATION_CHOICES = [('INALIMWA', 'Inalimwa (Cultivated)'), ('ASILI', 'Za Asili (Wild)')]
    local_harvest_season = models.CharField(max_length=100, blank=True, null=True, verbose_name="Msimu wa kuvuna (Local)")
    local_harvested_part = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sehemu inayovunwa (Local)")
    local_cultivated_or_wild = models.CharField(max_length=20, choices=CULTIVATION_CHOICES, blank=True, null=True)
    local_abundance = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hali ya upatikanaji (Local)")
    imported_countries = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nchi zinakotoka (Imported)")
    imported_plant_part = models.CharField(max_length=100, blank=True, null=True, verbose_name="Sehemu inayoingizwa (Imported)")
    imported_raw_state = models.CharField(max_length=255, blank=True, null=True, verbose_name="Hali ya dawaghafi inayoingizwa")
    imported_abundance = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hali ya upatikanaji (Imported)")

    # Manufacturing Information (Hatua ya 3)
    harvesting_method = models.TextField(verbose_name="Method of harvesting raw materials (Namna ya uvunaji wa malighafi)", blank=True, null=True)
    drying_procedures = models.TextField(verbose_name="Drying procedures (Namna ya ukaushaji)", blank=True, null=True)
    drying_area = models.CharField(max_length=255, blank=True, null=True, verbose_name="Sehemu unayokaushia")
    drying_equipment = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vifaa vya kukaushia")
    
    LOCATION_CHOICES = [('NDANI_YA_NYUMBA', 'Ndani ya nyumba ya kuishi'), ('LIMEJITENGA', 'Limejitenga na nyumba')]
    manufacturing_location_type = models.CharField(max_length=20, choices=LOCATION_CHOICES, blank=True, null=True)
    manufacturing_area_size = models.CharField(max_length=100, blank=True, null=True, verbose_name="Saizi ya eneo/jengo")
    manufacturing_procedures = models.TextField(verbose_name="Manufacturing procedures (Hatua za utengenezaji)", blank=True, null=True)
    equipment_used = models.TextField(verbose_name="Equipment used (Vifaa vinavyotumika)", blank=True, null=True)
    manufacturing_area = models.CharField(max_length=255, verbose_name="Manufacturing area (Eneo la uzalishaji)", blank=True, null=True)
    packaging_procedures = models.TextField(verbose_name="Packaging procedures (Namna ya ufungashaji)", blank=True, null=True)
    quality_control_procedures = models.TextField(verbose_name="Taratibu za udhibiti wa ubora (Quality control procedures)", blank=True, null=True)
    in_process_control_procedures = models.TextField(verbose_name="Hatua za udhibiti wakati wa uzalishaji (In-process control procedures)", blank=True, null=True)
    manufacturing_flow_chart = models.FileField(upload_to=medicine_document_path, verbose_name="Mchoro wa hatua za uzalishaji (Manufacturing flow chart)", blank=True, null=True)
    
    # Attachments (Hatua ya 4)
    # Note: "Sampuli tatu za dawa" is physical
    sample_label = models.FileField(upload_to=medicine_document_path, verbose_name="Sample medicine label (Mfano wa lebo ya dawa)", blank=True, null=True)
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

    # Status & Tracking
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    review_remarks = models.TextField(blank=True, null=True, help_text="General feedback from the staff evaluator")
    rejection_reason = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.medicine_name} ({self.get_application_type_display()}) - {self.applicant.email}"

    @property
    def registration_number(self):
        if self.id:
            year = self.updated_at.strftime('%y') if self.updated_at else '26'
            return f"TZ{year}TM{self.id:04d}"
        return None

    @property
    def requires_applicant_action(self):
        if self.status in ['DRAFT', 'CONDITIONS_APPLIED']:
            return True
        if 'PENDING' in self.status and 'FEE' in self.status:
            payments = list(self.payments.all())
            if payments:
                payment = payments[-1]
                if not payment.receipt_number and not payment.is_verified:
                    return True
        return False

    class Meta:
        ordering = ['-created_at']

