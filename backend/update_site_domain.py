import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site

def update_site():
    site, created = Site.objects.get_or_create(id=1)
    site.domain = 'live.tamris.org'
    site.name = 'TAMRIS TAHPC'
    site.save()
    print(f"Successfully updated Site ID 1 to domain: {site.domain}")

if __name__ == '__main__':
    update_site()
