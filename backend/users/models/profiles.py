from core.utils.uploads import user_document_path
from django.db import models
from django.core.validators import FileExtensionValidator, RegexValidator
from core.models import TimeStampedModel
from .base import CustomUser

class UserProfile(TimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile')
    full_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="First Name")
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Middle Name")
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Last Name")
    surname = models.CharField(max_length=100, blank=True, null=True, verbose_name="Surname / Jina la Ukoo")
    other_names = models.CharField(max_length=150, blank=True, null=True, verbose_name="Other Names / Majina Mengine")
    nida_number = models.CharField(
        max_length=50, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d{7}-\d{5}-\d{5}-\d{2}$',
                message='NIDA must be in the format YYYYMMDD-XXXXX-XXXXX-XX and cannot start with 0 (e.g., 19501007-11101-00001-26)'
            )
        ]
    )
    tin = models.CharField(
        max_length=100, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d{8}$',
                message='TIN must be exactly 9 digits and cannot start with 0.'
            )
        ]
    )
    
    # Demographic
    sex = models.CharField(
        max_length=10, 
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], 
        blank=True, 
        null=True
    )
    age = models.PositiveIntegerField(blank=True, null=True, verbose_name="Age")
    date_of_birth = models.DateField(blank=True, null=True)
    education_level = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Formal Education / Elimu (Rasmi)"
    )
    
    # Address
    country = models.CharField(max_length=100, default='Tanzania', verbose_name="Nationality / Country / Utaifa")
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Region / Mkoa")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="District / Wilaya")
    ward = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ward / Kata")
    village_street = models.CharField(max_length=150, blank=True, null=True, verbose_name="Village/Street / Kijiji au Mtaa")
    residency_duration = models.CharField(max_length=100, blank=True, null=True, verbose_name="Residency Duration / Muda wa Kuishi Mahali Hapo")
    postal_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Postal Address / Anuani ya Posta")
    address = models.TextField(blank=True, null=True, verbose_name="Physical Address")
    
    # Contacts
    landline_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telephone / Simu")
    alternative_contact = models.CharField(max_length=50, blank=True, null=True, verbose_name="Alternative Contact")
    fax = models.CharField(max_length=50, blank=True, null=True, verbose_name="Fax / Nukushi (Faksi)")
    
    # Documents
    nida_copy = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    passport_photo = models.ImageField(
        upload_to=user_document_path, 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    tahpc_certificate = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    tin_certificate = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        verbose_name="TIN Certificate Copy",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    @property
    def is_details_complete(self):
        has_name = bool(self.first_name or self.surname or self.full_name)
        has_phone = bool(self.user and self.user.phone_number)
        has_sex = bool(self.sex)
        return bool(has_name and has_phone and has_sex)

    @property
    def is_profile_complete(self):
        return bool(self.nida_copy)
        
    @property
    def formatted_nida(self):
        val = self.nida_number
        if not val: return val
        val = val.replace('-', '')
        if len(val) == 20:
            return f"{val[:8]}-{val[8:13]}-{val[13:17]}-{val[17:]}"
        return self.nida_number

    @property
    def formatted_tin(self):
        val = self.tin
        if not val: return val
        val = val.replace('-', '')
        if len(val) == 9:
            return f"{val[:3]}-{val[3:6]}-{val[6:]}"
        return self.tin

    def __str__(self):
        return self.full_name

class CompanyProfile(TimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=255, unique=True)
    brela_number = models.CharField(max_length=100, unique=True)
    tin = models.CharField(
        max_length=100, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d{8}$',
                message='TIN must be exactly 9 digits and cannot start with 0.'
            )
        ]
    )
    
    # Address
    country = models.CharField(max_length=100, default='Tanzania', verbose_name="Nationality / Country / Utaifa")
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Region / Mkoa")
    district = models.CharField(max_length=100, blank=True, null=True, verbose_name="District / Wilaya")
    ward = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ward / Kata")
    village_street = models.CharField(max_length=150, blank=True, null=True, verbose_name="Village/Street / Kijiji au Mtaa")
    postal_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Postal Address / Anuani ya Posta")
    physical_address = models.TextField(blank=True, null=True, verbose_name="Physical Address")
    
    # Contacts
    landline_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telephone / Simu")
    alternative_contact = models.CharField(max_length=50, blank=True, null=True, verbose_name="Alternative Contact")
    fax = models.CharField(max_length=50, blank=True, null=True, verbose_name="Fax / Nukushi (Faksi)")
    
    # Documents
    brela_certificate = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    tin_certificate = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    business_license = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    tahpc_certificate = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    representative_nida = models.FileField(
        upload_to=user_document_path, 
        blank=True, null=True,
        verbose_name="Representative NIDA (Kitambulisho cha NIDA cha Mwakilishi)",
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    representative_id_image = models.ImageField(
        upload_to=user_document_path, 
        blank=True, null=True,
        verbose_name="Representative ID/Passport Photo (Picha ya Mwakilishi)",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )

    @property
    def is_details_complete(self):
        has_name = bool(self.company_name)
        has_phone = bool(self.user and self.user.phone_number)
        has_tin = bool(self.tin)
        return bool(has_name and has_phone and has_tin)

    @property
    def is_profile_complete(self):
        return bool(
            self.brela_certificate and self.tin_certificate and self.business_license
        )

    @property
    def formatted_tin(self):
        val = self.tin
        if not val: return val
        val = val.replace('-', '')
        if len(val) == 9:
            return f"{val[:3]}-{val[3:6]}-{val[6:]}"
        return self.tin

    def __str__(self):
        return self.company_name

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
