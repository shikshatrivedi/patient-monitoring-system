import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from accounts.models import HospitalReferenceDoctor, DoctorProfile
from django.contrib.auth.models import User
from patients.models import Patient

def verify():
    print("--- VERIFICATION REPORT ---")
    
    # 1. Check HospitalReferenceDoctor counts and specializations
    ref_count = HospitalReferenceDoctor.objects.count()
    print(f"Total Reference Doctors: {ref_count}")
    
    specs = HospitalReferenceDoctor.objects.values('specialization').annotate(count=Count('id'))
    print("Specialization Status:")
    for s in specs:
        print(f" - {s['specialization']}: {s['count']}")
        
    # 2. Check for Arun and Vikram in Reference List
    arun_ref = HospitalReferenceDoctor.objects.filter(name__icontains='Arun Singh').exists()
    vikram_ref = HospitalReferenceDoctor.objects.filter(name__icontains='Vikram Joshi').exists()
    print(f"Arun Singh in Ref List: {'FOUND' if arun_ref else 'REMOVED'}")
    print(f"Vikram Joshi in Ref List: {'FOUND' if vikram_ref else 'REMOVED'}")
    
    # 3. Check for Arun and Vikram in User accounts
    arun_user = User.objects.filter(first_name__iexact='Arun', last_name__iexact='Singh').exists()
    vikram_user = User.objects.filter(first_name__iexact='Vikram', last_name__iexact='Joshi').exists()
    print(f"Arun Singh User Account: {'STILL EXISTS' if arun_user else 'REMOVED'}")
    print(f"Vikram Joshi User Account: {'STILL EXISTS' if vikram_user else 'REMOVED'}")
    
    # 4. Check Patients
    total_patients = Patient.objects.count()
    print(f"Total Patients in System: {total_patients}")
    
    print("\n--- CONCLUSION ---")
    if not arun_ref and not vikram_ref and not arun_user and not vikram_user:
        print("✅ SUCCESS: Doctors and their reference records have been cleanly removed.")
    else:
        print("❌ FAILURE: Some records still remain.")
        
    if all(s['specialization'] != '' for s in specs):
         print("✅ SUCCESS: All specializations have been updated.")
    else:
         print("⚠️ WARNING: Some specialization fields are still empty.")

if __name__ == '__main__':
    verify()
