import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from accounts.models import HospitalReferenceDoctor

def restore():
    print("--- RESTORING REMOVED REFERENCE DOCTORS ---")
    
    doctors_to_restore = [
        ("Dr. Arun Singh", "Primary Care Doctor", "HOSP-001", "Interventional Cardiology"),
        ("Dr. Vikram Joshi", "Primary Care Doctor", "HOSP-007", "Cosmetic Dermatology"),
    ]
    
    for name, dept, doc_id, spec in doctors_to_restore:
        obj, created = HospitalReferenceDoctor.objects.get_or_create(
            hospital_doc_id=doc_id,
            defaults={'name': name, 'department': dept, 'specialization': spec}
        )
        if created:
            print(f"✅ Restored: {name} ({doc_id})")
        else:
            obj.name = name
            obj.department = dept
            obj.specialization = spec
            obj.save()
            print(f"✅ Re-synchronized: {name} ({doc_id})")

    print("\n--- RESTORATION COMPLETED ---")

if __name__ == '__main__':
    restore()
