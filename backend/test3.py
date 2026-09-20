from django.conf import settings
settings.configure(USE_I18N=False)
import django
django.setup()
from django import forms
from django.db import models

class MockModel(models.Model):
    region = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        app_label = 'users'

class TestModelForm(forms.ModelForm):
    class Meta:
        model = MockModel
        fields = ['region']
        widgets = {
            'region': forms.Select(choices=[('', 'Select Region')])
        }

form = TestModelForm({'region': 'Dar es Salaam'})
print("Is valid?", form.is_valid())
if not form.is_valid():
    print("Errors:", form.errors)
