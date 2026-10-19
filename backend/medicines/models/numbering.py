from django.db import models, transaction


class NumberSequence(models.Model):
    """
    One counter per kind of number and per year. Certificate numbers and
    application references restart at 1 every January.
    """
    CERT_LISTING = 'CERT_LISTING'
    CERT_CATEGORY_II = 'CERT_CATEGORY_II'
    REF_LISTING = 'REF_LISTING'
    REF_CATEGORY_II = 'REF_CATEGORY_II'
    KIND_CHOICES = [
        (CERT_LISTING, 'Listing certificate number'),
        (CERT_CATEGORY_II, 'Category II registration certificate number'),
        (REF_LISTING, 'Listing application reference'),
        (REF_CATEGORY_II, 'Category II application reference'),
    ]

    kind = models.CharField(max_length=30, choices=KIND_CHOICES)
    year = models.PositiveIntegerField()
    last_number = models.PositiveIntegerField(default=0, help_text="The next number issued is this value plus one")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('kind', 'year')
        ordering = ['-year', 'kind']

    def __str__(self):
        return f"{self.get_kind_display()} {self.year}: {self.last_number}"

    @classmethod
    def _locked(cls, kind, year):
        cls.objects.get_or_create(kind=kind, year=year)
        return cls.objects.select_for_update().get(kind=kind, year=year)

    @classmethod
    def take_next(cls, kind, year):
        """Reserve and return the next number. Safe when two users act at the same moment."""
        with transaction.atomic():
            seq = cls._locked(kind, year)
            seq.last_number += 1
            seq.save(update_fields=['last_number', 'updated_at'])
            return seq.last_number

    @classmethod
    def ensure_at_least(cls, kind, year, number):
        """Move the counter past a number that was issued outside the system."""
        with transaction.atomic():
            seq = cls._locked(kind, year)
            if number > seq.last_number:
                seq.last_number = number
                seq.save(update_fields=['last_number', 'updated_at'])


class SystemSettings(models.Model):
    """Single row of settings the administrator can change from the System Settings page."""

    # Certificate numbers: TZ + 2-digit year + code + sequence
    category_ii_certificate_code = models.CharField(max_length=5, default='TM')
    listing_certificate_code = models.CharField(max_length=5, default='TL')
    certificate_digits = models.PositiveSmallIntegerField(default=4)

    # Application references: PREFIX/CODE/YEAR/SEQUENCE
    reference_prefix = models.CharField(max_length=20, default='TAHPC')
    listing_reference_code = models.CharField(max_length=10, default='LST')
    category_ii_reference_code = models.CharField(max_length=10, default='REG')

    # Images printed on certificates
    coat_of_arms = models.FileField(upload_to='settings/', blank=True, null=True)
    council_logo = models.FileField(upload_to='settings/', blank=True, null=True)
    chairman_signature = models.FileField(upload_to='settings/', blank=True, null=True)
    registrar_signature = models.FileField(upload_to='settings/', blank=True, null=True)
    council_seal = models.FileField(upload_to='settings/', blank=True, null=True)

    # Mandatory documents (field names / document types)
    mandatory_listing_documents = models.JSONField(default=list, blank=True)
    mandatory_category_ii_documents = models.JSONField(default=list, blank=True)
    mandatory_individual_documents = models.JSONField(default=list, blank=True)
    mandatory_company_documents = models.JSONField(default=list, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    DEFAULT_MANDATORY = {
        'mandatory_listing_documents': ['sample_label', 'ingredients_info_doc'],
        'mandatory_category_ii_documents': ['scientific_name_report'],
        'mandatory_individual_documents': [],
        'mandatory_company_documents': ['brela_certificate', 'tin_certificate', 'business_license'],
    }

    class Meta:
        verbose_name = 'System settings'
        verbose_name_plural = 'System settings'

    def __str__(self):
        return 'System settings'

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create(**cls.DEFAULT_MANDATORY)
        return obj
