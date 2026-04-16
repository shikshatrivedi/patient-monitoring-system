from django.db import models
from patients.models import Patient
from django.contrib.auth.models import User
from django.utils import timezone

# 1. Live Vitals Table (Used for the dashboard real-time view)
class PatientVitals(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    bpm = models.IntegerField(default=0)
    spo2 = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    # Flag to distinguish seeded demo data from real Arduino data
    is_seeded = models.BooleanField(default=False)

    def __str__(self):
        return f"Vitals for {self.patient.first_name} at {self.timestamp}"


# 2. Hardware Configuration (Singleton — stores COM port & baud rate)
class HardwareConfig(models.Model):
    """
    Singleton model. Only one row (pk=1) ever exists.
    Stores the COM port and baud rate set from the configuration page.
    """
    port = models.CharField(max_length=20, default='COM3')
    baud_rate = models.IntegerField(default=115200)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Enforce singleton — always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'port': 'COM3', 'baud_rate': 115200})
        return obj

    def __str__(self):
        return f"HardwareConfig: {self.port} @ {self.baud_rate} baud"


# 3. Hardware Connection Status (Singleton — tracks live Arduino state)
class HardwareStatus(models.Model):
    """
    Singleton model. Only one row (pk=1) ever exists.
    Written by hardware_bridge.py to reflect real Arduino connection state.
    """
    connected = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Enforce singleton — always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_status(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'connected': False})
        return obj

    def __str__(self):
        state = "Connected" if self.connected else "Disconnected"
        return f"Hardware: {state}"


# 4. Active Monitoring State (Singleton — tracks which patient is being watched)
class ActiveMonitoring(models.Model):
    active_patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        if self.active_patient:
            return f"Active: {self.active_patient.first_name}"
        return "No Active Patient"


# NOTE: PatientHistory class is inside patients/models.py


# 5. Medical Report Storage (Saves generated PDF reports)
class MedicalReport(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='reports')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    pdf_file = models.FileField(upload_to='reports/')
    summary = models.CharField(max_length=255, default='Medical Report')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"Report for {self.patient.full_name} - {self.generated_at.strftime('%d %b %Y')}"