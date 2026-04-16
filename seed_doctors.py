"""
seed_doctors.py
Run with: venv\Scripts\python.exe seed_doctors.py

Obj 0: Deletes ALL existing doctor accounts (DoctorProfile + User) except superusers/admins.
Obj 3: Creates 100 new approved doctors with DOC001–DOC100 IDs.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import DoctorProfile

# ============================================================
# STEP 0: DELETE ALL EXISTING DOCTORS
# (Only doctor-role DoctorProfiles + their linked Users)
# Does NOT touch patients, alerts, reports, or admin/superusers.
# ============================================================

print("=" * 60)
print("STEP 0: Deleting all existing doctor accounts...")
print("=" * 60)

doctor_profiles = DoctorProfile.objects.filter(role='doctor')
deleted_count = 0

for profile in doctor_profiles:
    username = profile.user.username
    profile.user.delete()   # CASCADE deletes the DoctorProfile too
    print(f"  ✂  Deleted: {username}")
    deleted_count += 1

print(f"\n  ✅ Deleted {deleted_count} doctor account(s).\n")


# ============================================================
# STEP 3: CREATE 100 NEW APPROVED DOCTORS
# Hospital: City Medical Center
# ============================================================

DEPARTMENTS = [
    "General Medicine",
    "Internal Medicine",
    "Cardiology",
    "Neurology",
    "Pulmonology",
    "Orthopedics",
    "Gastroenterology",
    "Endocrinology",
    "Nephrology",
    "Dermatology",
]

FIRST_NAMES = [
    "Arjun","Priya","Rahul","Sneha","Amit","Kavya","Rohit","Anjali",
    "Vikram","Meera","Sanjay","Pooja","Kiran","Divya","Suresh","Nisha",
    "Manish","Rekha","Deepak","Sunita","Aakash","Simran","Rajesh","Geeta",
    "Nikhil","Shruti","Vivek","Lakshmi","Mohit","Radha","Ashish","Poonam",
    "Gaurav","Anita","Sachin","Swati","Hemant","Bharti","Kunal","Ritu",
    "Abhishek","Shilpa","Tarun","Smita","Varun","Preeti","Bhaskar","Mamta",
    "Dhruv","Kamala",
]

LAST_NAMES = [
    "Sharma","Verma","Patel","Singh","Gupta","Joshi","Mehta","Yadav",
    "Mishra","Agarwal","Reddy","Nair","Pillai","Iyer","Kulkarni","Bose",
    "Chatterjee","Das","Sen","Roy","Malhotra","Kapoor","Chopra","Khanna",
    "Srivastava","Pandey","Tripathi","Tiwari","Rao","Kumar",
]

print("=" * 60)
print("STEP 3: Creating 100 new approved doctors...")
print("=" * 60)

created_count = 0

for i in range(1, 101):
    doc_id   = f"DOC{i:03d}"
    fname    = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
    lname    = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
    dept     = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
    username = f"dr_{fname.lower()}_{i}"
    email    = f"{username}@citymedical.com"
    mobile   = f"98{i:08d}"[:15]
    password = f"Doctor@{i:03d}"

    # Skip if username already exists (safety check)
    if User.objects.filter(username=username).exists():
        print(f"  ⚠  Skipped (already exists): {username}")
        continue

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=fname,
        last_name=lname,
    )

    DoctorProfile.objects.create(
        user=user,
        mobile_number=mobile,
        role='doctor',
        doctor_status='approved',
        doctor_id=doc_id,
    )

    created_count += 1
    print(f"  ✅ {doc_id}  {fname} {lname}  ({dept})  [{username}]")

print()
print("=" * 60)
print(f"DONE — Created {created_count} doctors.")
print("=" * 60)
print()
print("Departments used:")
for d in DEPARTMENTS:
    print(f"  • {d}")
print()
print("Login credentials pattern: dr_<name>_<N> / Doctor@<NNN>")
print("Example: username=dr_arjun_1  password=Doctor@001")
