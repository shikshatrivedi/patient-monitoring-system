import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms_core.settings")
django.setup()
settings.ALLOWED_HOSTS.append('testserver')

from django.test import Client
from django.contrib.auth.models import User

def test_view():
    print("Testing register_view via Client...")
    
    # Ensure clean state
    User.objects.filter(username='testviewuser').delete()
    
    c = Client()
    
    # Valid submission
    response = c.post('/accounts/register/', {
        'username': 'testviewuser',
        'email': 'testview@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'degree': 'MBBS',
        'mobile_number': '1112223333',
        'department': 'General Medicine'
    })
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 302:
        print("Redirected (Success)")
        print(f"Location: {response.url}")
    elif response.status_code == 200:
        print("Form Error (Failed)")
        # Check context for errors
        if 'form' in response.context:
            print(f"Format Errors: {response.context['form'].errors.as_text()}")
    else:
        print(f"Unexpected status: {response.status_code}")

if __name__ == "__main__":
    test_view()
