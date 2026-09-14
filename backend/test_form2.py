import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.forms.profiles import CustomUserCreationForm

form = CustomUserCreationForm(data={'email': 'test2@example.com', 'phone_number': '0788-123-456'})
form.data['password1'] = 'Testpass123!'
form.data['password2'] = 'Testpass123!'

print("Is valid:", form.is_valid())
print("Errors:", form.errors)
print("Cleaned data:", form.cleaned_data if form.is_valid() else None)
