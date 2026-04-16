import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import HospitalReferenceDoctor, DoctorProfile
from patients.models import Patient

def run():
    print("--- STEP 1: Updating Specializations in HospitalReferenceDoctor ---")
    # Using the mapping provided by the user
    for doc in HospitalReferenceDoctor.objects.all():
        if doc.department == 'Primary Care Doctor':
            doc.specialization = 'General Checkup Specialist'
        elif doc.department == 'Internal Medicine Specialist':
            doc.specialization = 'Internal Medicine Specialist'
        elif doc.department == 'Clinical Physician':
            doc.specialization = 'Clinical Care Specialist'
        elif doc.department == 'Family Medicine Doctor':
            doc.specialization = 'Family Health Specialist'
        elif doc.department == 'Medical Officer':
            doc.specialization = 'Emergency Care Specialist'
        else:
            doc.specialization = 'General Physician'
        doc.save()
    print("✅ Specializations updated.")

    print("\n--- STEP 2: Removing Arun Singh and Vikram Joshi from Reference List ---")
    ref_deleted_count, _ = HospitalReferenceDoctor.objects.filter(
        name__icontains='Arun Singh'
    ).delete()
    ref_deleted_count += HospitalReferenceDoctor.objects.filter(
        name__icontains='Vikram Joshi'
    ).delete()[0]
    print(f"✅ Deleted {ref_deleted_count} records from HospitalReferenceDoctor.")

    print("\n--- STEP 3: Removing System Accounts and Related Patients (to allow re-registration) ---")
    # Search for users matching the names
    users_to_delete = User.objects.filter(
        first_name__iexact='Arun', last_name__iexact='Singh'
    ) | User.objects.filter(
        first_name__iexact='Vikram', last_name__iexact='Joshi'
    )

    for user in users_to_delete:
        username = user.username
        # Find patients assigned to this doctor
        patients = Patient.objects.filter(assigned_doctor=user)
        patient_count = patients.count()
        patients.delete()
        print(f"   - Deleted {patient_count} patients assigned to {username}")
        
        # Delete user (cascades to DoctorProfile)
        user.delete()
        print(f"   - Deleted User account: {username}")

    print("✅ System accounts and related patients cleared.")
    print("\n--- ALL TASKS COMPLETED SUCCESSFULLY ---")

if __name__ == '__main__':
    run()
