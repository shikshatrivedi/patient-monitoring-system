"""
seed_demo_vitals.py
===================
Populates PatientVitals with 7 days of realistic historical data for every
active patient.  Run once before a demo:

    python seed_demo_vitals.py

SAFE TO RE-RUN — patients who already have 100+ readings are skipped.
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from patients.models import Patient
from monitor.models import PatientVitals
from django.utils import timezone

# ----------------------------------------------------------------
# Condition-based vitals ranges (mirrors hardware_bridge.py)
# ----------------------------------------------------------------
CONDITION_BASELINES = {
    'Normal':      {'hr_min': 78,  'hr_max': 85,  'spo2_min': 96, 'spo2_max': 99},
    'Observation': {'hr_min': 85,  'hr_max': 95,  'spo2_min': 93, 'spo2_max': 96},
    'Critical':    {'hr_min': 95,  'hr_max': 110, 'spo2_min': 88, 'spo2_max': 94},
}

READINGS_PER_DAY = 24   # one reading per hour per day
DAYS_BACK        = 7    # one full week of history


def seed_patient(patient):
    existing = PatientVitals.objects.filter(patient=patient).count()
    if existing >= 100:
        print(f"  ⏭  {patient.full_name} already has {existing} readings — skipped")
        return

    condition = patient.condition or 'Normal'
    ranges    = CONDITION_BASELINES.get(condition, CONDITION_BASELINES['Normal'])

    # Start from the middle of the condition range
    hr   = (ranges['hr_min']   + ranges['hr_max'])   // 2
    spo2 = (ranges['spo2_min'] + ranges['spo2_max']) // 2

    now   = timezone.now()
    start = now - timedelta(days=DAYS_BACK)

    bulk = []
    total_readings = DAYS_BACK * READINGS_PER_DAY

    for i in range(total_readings):
        # ±1 smooth walk clamped to range
        hr   += random.choice([-1, 0, 0, 1])
        spo2 += random.choice([-1, 0, 0, 1])

        hr   = max(ranges['hr_min'],   min(ranges['hr_max'],   hr))
        spo2 = max(ranges['spo2_min'], min(ranges['spo2_max'], spo2))

        ts = start + timedelta(hours=i)
        bulk.append(PatientVitals(patient=patient, bpm=hr, spo2=spo2, timestamp=ts))

    PatientVitals.objects.bulk_create(bulk)
    print(f"  ✅  {patient.full_name} [{condition}]: {len(bulk)} readings seeded "
          f"(HR {ranges['hr_min']}–{ranges['hr_max']}, SpO2 {ranges['spo2_min']}–{ranges['spo2_max']})")


def main():
    patients = Patient.objects.filter(is_active=True)
    if not patients.exists():
        print("❌ No active patients found. Register patients first.")
        sys.exit(1)

    print(f"\n🌱 Seeding demo vitals for {patients.count()} active patient(s)...\n")
    for p in patients:
        seed_patient(p)

    print("\n✅ Seed complete! Charts will now be populated on the monitoring dashboard.\n")


if __name__ == '__main__':
    main()
