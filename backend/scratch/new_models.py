from core.utils.uploads import user_document_path
from django.db import models
from django.core.validators import FileExtensionValidator, RegexValidator
from core.models import TimeStampedModel
from .base import CustomUser

class Applicant(TimeStampedModel):
    APPLICANT_TYPES = [
        ('Individual', 'Individual'),
        ('Organization', 'Organization'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='applicant_profile')
    applicant_type = models.CharField(max_length=20, choices=APPLICANT_TYPES)
    application_no = models.CharField(max_length=50, blank=True, null=True, unique=True)
    status = models.CharField(max_length=50, default='Draft')

    @property
    def is_details_complete(self):
        if self.applicant_type == 'Individual':
            if hasattr(self, 'individual'):
                has_name = bool(self.individual.first_name or self.individual.last_name)
                has_sex = bool(self.individual.sex)
                return has_name and has_sex
        elif self.applicant_type == 'Organization':
            if hasattr(self, 'organization'):
                has_name = bool(self.organization.organization_name)
                has_tin = bool(self.organization.tin)
                return has_name and has_tin
        return False

    def __str__(self):
        return f"{self.user.email} - {self.applicant_type}"

class Individual(TimeStampedModel):
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='individual')
    first_name = models.CharField(max_length=100, verbose_name="First Name")
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Middle Name")
    last_name = models.CharField(max_length=100, verbose_name="Last Name")
    sex = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    @property
    def full_name(self):
        return " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))

    def __str__(self):
        return self.full_name

class Organization(TimeStampedModel):
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE, related_name='organization')
    organization_name = models.CharField(max_length=255, unique=True)
    organization_type = models.CharField(max_length=100, blank=True, null=True)
    registration_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    tin = models.CharField(
        max_length=100, 
        unique=True,
        blank=True, null=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d{8}$',
                message='TIN must be exactly 9 digits and cannot start with 0.'
            )
        ]
    )
    year_established = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        return self.organization_name

class ApplicantIdentity(TimeStampedModel):
    ID_CHOICES = [
        ('NIDA (National ID)', 'NIDA (National ID)'),
        ('Passport (Hati ya kusafiria)', 'Passport (Hati ya kusafiria)'),
        ('Driver\'s License', 'Driver\'s License'),
        ('Voter\'s ID', 'Voter\'s ID'),
    ]
    
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='identities')
    identity_type = models.CharField(max_length=50, choices=ID_CHOICES, verbose_name="ID Type")
    identity_number = models.CharField(max_length=100, verbose_name="ID Number")
    is_primary = models.BooleanField(default=False)

    @property
    def formatted_id_number(self):
        val = self.identity_number
        if not val: return val
        if self.identity_type == 'NIDA (National ID)':
            val = val.replace('-', '')
            if len(val) == 20:
                return f"{val[:8]}-{val[8:13]}-{val[13:17]}-{val[17:]}"
        return val

    def __str__(self):
        return f"{self.identity_type} - {self.identity_number}"

class ApplicantAddress(TimeStampedModel):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=50, default='Physical')
    country = models.CharField(max_length=100, default='Tanzania', verbose_name="Nationality / Country / Utaifa")
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Region / Mkoa")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="District / Wilaya")
    ward = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ward / Kata")
    street = models.CharField(max_length=150, blank=True, null=True, verbose_name="Village/Street / Kijiji au Mtaa")
    physical_address = models.TextField(blank=True, null=True, verbose_name="Physical Address")
    postal_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Postal Address / Anuani ya Posta")

class ApplicantContact(TimeStampedModel):
    CONTACT_CHOICES = [
        ('Phone', 'Phone'),
        ('Email', 'Email'),
        ('Fax', 'Fax'),
    ]
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=50, choices=CONTACT_CHOICES, default='Phone')
    contact_value = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)

class Education(TimeStampedModel):
    EDUCATION_LEVEL_CHOICES = [
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('Vocational/Technical', 'Vocational/Technical'),
        ('Certificate', 'Certificate'),
        ('Diploma', 'Diploma'),
        ('Bachelor\'s Degree', 'Bachelor\'s Degree'),
        ('Postgraduate', 'Postgraduate'),
        ('Doctorate', 'Doctorate'),
    ]
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='educations')
    education_level = models.CharField(
        max_length=100,
        choices=EDUCATION_LEVEL_CHOICES,
        blank=True, 
        null=True,
        verbose_name="Formal Education / Elimu (Rasmi)"
    )

class OrganizationRepresentative(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='representatives')
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    identity_type = models.CharField(max_length=50, choices=ApplicantIdentity.ID_CHOICES, blank=True, null=True)
    identity_number = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

class ApplicantDocument(TimeStampedModel):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=100)
    file = models.FileField(
        upload_to=user_document_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

class StaffProfile(TimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

    @property
    def is_profile_complete(self):
        return True

    def __str__(self):
        return f"{self.user.email} - {self.designation}"
