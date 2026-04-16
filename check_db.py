import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from patients.models import Patient

print("Checking Patient Data:")
for p in Patient.objects.all():
    print(f"ID: {p.id}")
    print(f"First Name: '{p.first_name}'")
    print(f"Last Name: '{p.last_name}'")
    print("-" * 20)
