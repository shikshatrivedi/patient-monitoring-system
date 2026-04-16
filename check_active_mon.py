import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from monitor.models import ActiveMonitoring

active_mon = ActiveMonitoring.get_active()
patient = active_mon.active_patient

if patient:
    print(f"Active Patient: {patient.first_name} {patient.last_name} (ID: {patient.id})")
else:
    print("No active patient being monitored.")
