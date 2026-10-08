from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # Public-facing URLs to be indexed by Google
        return [
            'users:frontend_login',
            'users:frontend_register',
            'users:password_reset',
        ]

    def location(self, item):
        return reverse(item)
