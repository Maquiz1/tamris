import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.forms.profiles import CustomUserCreationForm

form = CustomUserCreationForm(data={'email': 'test@example.com', 'phone_number': '0788-123-456'})
print("Is valid:", form.is_valid())
print("Errors:", form.errors)
print("Cleaned data:", form.cleaned_data if form.is_valid() else None)
