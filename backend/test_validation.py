import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django import forms

class TestForm(forms.Form):
    region = forms.CharField(widget=forms.Select(choices=[('', 'Select Region')]))

form = TestForm({'region': 'Dar es Salaam'})
print("Is valid?", form.is_valid())
if not form.is_valid():
    print("Errors:", form.errors)
