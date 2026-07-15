from django.db import models
from django.conf import settings
from core.models import TimeStampedModel, ActivableModel
from core.utils.fees import FEE_TYPES
from .applications import MedicineApplication

class Payment(TimeStampedModel):
    application = models.ForeignKey(MedicineApplication, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=50, choices=FEE_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Kiasi (Amount in TZS)")
    receipt_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Namba ya Risiti / Control Number")
    
    is_verified = models.BooleanField(default=False, verbose_name="Imethibitishwa? (Verified?)")
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True, verbose_name="Maoni (Remarks)")

    def __str__(self):
        return f"{self.get_payment_type_display()} for {self.application.medicine_name}"

class FeeInactiveError(Exception):
    """Exception raised when a requested fee configuration is marked as inactive."""
    pass

class FeeConfiguration(TimeStampedModel, ActivableModel):
    fee_type = models.CharField(max_length=50, choices=FEE_TYPES, unique=True, verbose_name="Aina ya Ada (Fee Type)")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Kiasi (Amount in TZS)")

    def __str__(self):
        return f"{self.get_fee_type_display()} - {self.amount} TZS"

    @property
    def short_name(self):
        full_name = self.get_fee_type_display()
        if ': ' in full_name:
            part = full_name.split(': ', 1)[1]
            if part[0].isdigit() and part[1:3] == '. ':
                return part[3:]
            return part
        return full_name

    @classmethod
    def get_fee(cls, fee_type_code, default_amount=0.00):
        obj, created = cls.objects.get_or_create(
            fee_type=fee_type_code,
            defaults={'amount': default_amount}
        )
        if not obj.is_active:
            raise FeeInactiveError(f"Fee {fee_type_code} is currently suspended/inactive.")
        return obj.amount
