from django import forms
from medicines.models import Payment, FeeConfiguration

class PaymentVerificationForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['is_verified', 'remarks']
        widgets = {
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Remarks on Payment...'}),
        }

class ApplicantPaymentSubmissionForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['receipt_number']
        widgets = {
            'receipt_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Bank Receipt Number or Control Number'}),
        }

class FeeConfigurationForm(forms.ModelForm):
    class Meta:
        model = FeeConfiguration
        fields = ['fee_type', 'amount', 'is_active']
        widgets = {
            'fee_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean(self):
        cleaned_data = super().clean()
        fee_type = cleaned_data.get('fee_type')
        
        # We only care about modifications
        if self.instance and self.instance.pk:
            if 'amount' in self.changed_data or 'is_active' in self.changed_data:
                from medicines.models import Payment
                
                if fee_type:
                    if Payment.objects.filter(payment_type=fee_type, is_verified=False).exists():
                        raise forms.ValidationError("Cannot modify this fee because there are active applications currently processing this payment.")
                        
        return cleaned_data

