import os
import django
import random
from math import sin, pi
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from patients.models import Patient
from monitor.models import PatientVitals

def seed_vitals():
    print("Starting vital seeding process...")
    # 1. Clear existing seeded data to avoid duplicates
    deleted_count, _ = PatientVitals.objects.filter(is_seeded=True).delete()
    print(f"Cleaned up {deleted_count} old seeded records.")
    
    patients = Patient.objects.all()
    if not patients.exists():
        print("No patients found in database. Please register patients first.")
        return

    for patient in patients:
        print(f"Seeding for {patient.full_name} (Condition: {patient.condition})...")
        
        cond = patient.condition
        if cond == 'Critical':
            hr_base, hr_var = 95, 15
            spo2_base, spo2_var = 88, 6
        elif cond in ['Observation', 'Fever', 'Continuous Monitoring']:
            hr_base, hr_var = 85, 15
            spo2_base, spo2_var = 92, 4
        else: # Normal
            hr_base, hr_var = 75, 7
            spo2_base, spo2_var = 96, 3
            
        now = timezone.now()
        vitals_to_create = []
        
        # We need data for the last 7 days to fill the weekly chart.
        # Let's seed 500 rows total, spaced 20 minutes apart.
        # 500 * 20 mins = 10,000 mins = ~7 days.
        total_rows = 500
        for i in range(total_rows):
            angle = (i / 15) * pi 
            hr = int(hr_base + (hr_var / 2) * (1 + sin(angle)) + random.randint(-1, 1))
            spo2 = int(spo2_base + (spo2_var / 2) * (1 + sin(angle + pi/4)) + random.randint(0, 1))
            spo2 = min(100, spo2)
            
            # Each row is +20 minutes apart to cover 7 days
            ts = now - timedelta(minutes=20 * (total_rows - i))
            
            vitals_to_create.append(PatientVitals(
                patient=patient,
                bpm=hr,
                spo2=spo2,
                timestamp=ts,
                is_seeded=True
            ))
            
        PatientVitals.objects.bulk_create(vitals_to_create)
        print(f"  Inserted {total_rows} rows for {patient.first_name} covering 7 days.")

    print("\nSuccess: SQLite Master Database seeded with smooth 7-day vitals.")

if __name__ == "__main__":
    seed_vitals()
