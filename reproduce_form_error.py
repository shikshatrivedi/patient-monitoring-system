import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pms_core.settings")
django.setup()

from accounts.forms import RegistrationForm

def test_form():
    print("Testing RegistrationForm...")
    
    # Case 1: All fields present
    data_valid = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'degree': 'MBBS',
        'mobile_number': '1234567890',
        'department': 'General Medicine'
    }
    print(f"Form fields: {list(RegistrationForm().fields.keys())}")
    
    form = RegistrationForm(data=data_valid)
    print(f"Bound data keys: {list(form.data.keys())}")
    
    if form.is_valid():
        print("Case 1: VALID")
    else:
        print("Case 1: INVALID")
        # Write errors to a file because stdout is flaky
        with open('error_log.txt', 'w') as f:
            f.write(form.errors.as_text())
        print("Errors written to error_log.txt")

if __name__ == "__main__":
    test_form()
