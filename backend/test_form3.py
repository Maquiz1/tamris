import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.forms.profiles import CustomUserCreationForm

form = CustomUserCreationForm(data={'email': 'test3@example.com', 'phone_number': '0788-123-456'})
form.data['password1'] = 'Testpass123!'
form.data['password2'] = 'Testpass123!'

if form.is_valid():
    user = form.save(commit=False)
    print("Phone on user:", user.phone_number)
    try:
        user.full_clean()
        print("full_clean passed!")
    except Exception as e:
        print("full_clean failed:", e)
else:
    print("Form invalid:", form.errors)

