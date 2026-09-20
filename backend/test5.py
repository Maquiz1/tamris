from django.conf import settings
settings.configure(USE_I18N=False)
import django
django.setup()
from django import forms
from django.db import models
from django.forms import inlineformset_factory

class MockParent(models.Model):
    class Meta: app_label = 'users'

class MockModel(models.Model):
    parent = models.ForeignKey(MockParent, on_delete=models.CASCADE)
    region = models.CharField(max_length=100, blank=True, null=True)
    class Meta: app_label = 'users'

MockFormSet = inlineformset_factory(
    MockParent, MockModel,
    fields=['region'],
    extra=1,
    can_delete=True,
    widgets={'region': forms.Select(choices=[('', 'Select Region')])}
)

parent = MockParent()
data = {
    'users-mockmodel-content_type-object_id-TOTAL_FORMS': '1',
    'users-mockmodel-content_type-object_id-INITIAL_FORMS': '0',
    'users-mockmodel-content_type-object_id-MIN_NUM_FORMS': '0',
    'users-mockmodel-content_type-object_id-MAX_NUM_FORMS': '1000',
    'users-mockmodel-content_type-object_id-0-region': 'Dar es Salaam',
}
fset = MockFormSet(data, instance=parent)
print("Is valid?", fset.is_valid())
if not fset.is_valid():
    print("Errors:", fset.errors)
    print("Non form errors:", fset.non_form_errors())
