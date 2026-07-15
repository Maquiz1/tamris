from core.utils.uploads import user_document_path
from django.db import models
from django.core.validators import FileExtensionValidator, RegexValidator
from core.models import TimeStampedModel
from .base import CustomUser

class UserProfile(TimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile')
    full_name = models.CharField(max_length=255)
    nida_number = models.CharField(
        max_length=50, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d{7}-\d{5}-\d{4}-\d{3}$',
                message='NIDA must be in the format YYYYMMDD-XXXXX-XXXX-XXX and cannot start with 0 (e.g., 19810822-61218-9000-125)'
            )
        ]
    )
    tin = models.CharField(
        max_length=100, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[1-9]\d{2}-\d{3}-\d{3}$',
                message='TIN must be in the format XXX-XXX-XXX and cannot start with 0 (e.g., 123-456-909)'
            )
        ]
    )
    address = models.TextField(blank=True, null=True)
    
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
    def is_profile_complete(self):
        return bool(self.nida_copy and self.passport_photo and self.tahpc_certificate and self.tin_certificate)
        
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
                regex=r'^[1-9]\d{2}-\d{3}-\d{3}$',
                message='TIN must be in the format XXX-XXX-XXX and cannot start with 0 (e.g., 123-456-909)'
            )
        ]
    )
    physical_address = models.TextField(blank=True, null=True)
    
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
    def is_profile_complete(self):
        return bool(
            self.brela_certificate and self.tin_certificate and 
            self.business_license and self.tahpc_certificate and
            self.representative_nida and self.representative_id_image
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
