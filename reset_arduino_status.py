import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'pms_core.settings'
django.setup()
from monitor.models import HardwareStatus
hw = HardwareStatus.get_status()
hw.connected = False
hw.last_seen = None
hw.save()
print("Arduino status reset to DISCONNECTED.")
