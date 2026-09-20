import os
import sys
import django
from html.parser import HTMLParser

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from users.models import CustomUser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_form = False
        self.form_count = 0
    
    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            self.in_form = True
            self.form_count += 1
            print(f"Start Form {self.form_count}")
        elif tag == 'input':
            attr_dict = dict(attrs)
            if 'TOTAL_FORMS' in attr_dict.get('name', ''):
                if self.in_form:
                    print(f"  Inside form {self.form_count}: {attr_dict.get('name')}")
                else:
                    print(f"  OUTSIDE form: {attr_dict.get('name')}")
                    
    def handle_endtag(self, tag):
        if tag == 'form':
            self.in_form = False
            print(f"End Form {self.form_count}")

c = Client()
user = CustomUser.objects.filter(role__name='Company Applicant').first()
if user:
    c.force_login(user)
    response = c.get('/onboarding/?step=2')
    html = response.content.decode()
    parser = MyHTMLParser()
    parser.feed(html)
