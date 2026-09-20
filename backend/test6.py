from django.conf import settings
settings.configure(USE_I18N=False)
import django
django.setup()
from django import forms

class TestForm(forms.Form):
    region = forms.CharField(widget=forms.Select(attrs={'required': 'required'}))

form = TestForm()
print(form['region'])
