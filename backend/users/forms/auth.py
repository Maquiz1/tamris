from django import forms
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'autofocus': True}))

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, label='Enter 6-digit OTP')

