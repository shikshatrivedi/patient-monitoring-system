import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'pms_core.settings'
django.setup()
from accounts.models import DoctorProfile
docs = DoctorProfile.objects.filter(role='doctor')
print(f"Total doctors: {docs.count()}")
print(f"Approved: {docs.filter(doctor_status='approved').count()}")
print(f"Pending: {docs.filter(doctor_status='pending').count()}")
first5 = docs.values_list('doctor_id','user__username')[:5]
last5  = docs.values_list('doctor_id','user__username')[95:]
print("First 5:", list(first5))
print("Last 5:",  list(last5))
