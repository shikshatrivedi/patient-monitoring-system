import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from monitor.models import HardwareConfig

config = HardwareConfig.get_config()
print(f"Current Port: {config.port}")
print(f"Current Baud Rate: {config.baud_rate}")
