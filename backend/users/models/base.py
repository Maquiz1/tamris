from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator, RegexValidator
from core.models import TimeStampedModel

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class Role(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser, TimeStampedModel):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^0\d{3}-\d{3}-\d{3}$',
                message='Phone number must be in the format 0XXX-XXX-XXX (e.g., 0789-653-278)'
            )
        ]
    )
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    additional_roles = models.ManyToManyField(Role, related_name='secondary_users', blank=True)
    
    # OTP/Verification fields
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    phone_otp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_onboarding_complete = models.BooleanField(default=False)

    # Status tracking for staff review
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]
    registration_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection")
    review_remarks = models.TextField(blank=True, null=True, help_text="Overall remarks from the evaluator")
    document_statuses = models.JSONField(blank=True, null=True, default=dict, help_text="Stores status per document: {'nida_copy': {'status': 'VERIFIED', 'reason': ''}}")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.otp_secret:
            import pyotp
            self.otp_secret = pyotp.random_base32()
        super().save(*args, **kwargs)

    @property
    def formatted_phone(self):
        val = self.phone_number
        if not val: return val
        val = val.replace('-', '')
        if len(val) == 10:
            return f"{val[:4]}-{val[4:7]}-{val[7:]}"
        return self.phone_number

    @property
    def onboarding_step(self):
        if self.is_superuser or self.is_staff:
            return 5
        if not self.role:
            return 1
            
        # Staff bypasses onboarding completely
        if self.role.name in ['Evaluator', 'Inspector', 'Accountant', 'Admin']:
            return 5
        
        # Step 2: Needs Details (Profile Creation)
        if self.role.name == 'Individual Applicant':
            if not hasattr(self, 'user_profile'):
                return 2
            # Step 3: Needs Documents
            if not self.user_profile.is_profile_complete:
                return 3
        elif self.role.name == 'Company Applicant':
            if not hasattr(self, 'company_profile'):
                return 2
            # Step 3: Needs Documents
            if not self.company_profile.is_profile_complete:
                return 3
        
        # Step 4: Needs Review & Submit
        if not self.is_onboarding_complete:
            return 4
            
        return 5

    @property
    def all_roles(self):
        roles = []
        if self.role:
            roles.append(self.role.name)
        for r in self.additional_roles.all():
            roles.append(r.name)
        return roles

    @property
    def is_admin(self):
        return 'Admin' in self.all_roles or self.is_superuser

    @property
    def is_evaluator(self):
        return 'Evaluator' in self.all_roles

    @property
    def is_inspector(self):
        return 'Inspector' in self.all_roles

    @property
    def is_accountant(self):
        return 'Accountant' in self.all_roles

    @property
    def is_finance(self):
        return self.is_accountant
        
    @property
    def is_staff_member(self):
        """Check if user has any staff role."""
        return self.is_staff or self.is_admin or self.is_evaluator or self.is_inspector or self.is_finance or self.is_superuser

    @property
    def is_applicant(self):
        # Allow access if role is assigned OR if the user completed registration
        # (has a profile) — covers new applicants pending evaluator review.
        has_role = 'Individual Applicant' in self.all_roles or 'Company Applicant' in self.all_roles
        has_profile = hasattr(self, 'user_profile') or hasattr(self, 'company_profile')
        return has_role or has_profile or self.is_superuser or 'Admin' in self.all_roles

    @property
    def display_name(self):
        if hasattr(self, 'user_profile') and self.user_profile:
            return self.user_profile.full_name
        elif hasattr(self, 'company_profile') and self.company_profile:
            return self.company_profile.company_name
        
        full_name = self.get_full_name().strip()
        if full_name:
            return full_name
            
        return self.email

    @property
    def profile_photo_url(self):
        if hasattr(self, 'user_profile') and self.user_profile and self.user_profile.passport_photo:
            return self.user_profile.passport_photo.url
        if hasattr(self, 'company_profile') and self.company_profile and self.company_profile.representative_id_image:
            return self.company_profile.representative_id_image.url
        return None

    def __str__(self):
        return self.email

