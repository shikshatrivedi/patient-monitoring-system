from django.db import models
# ------------------------
from django.contrib.auth.models import User
from django.utils import timezone

class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    
    # This maps to 'purpose' in your form
    CONDITION_CHOICES = [
        ('Normal', 'Normal'),
        ('Observation', 'Observation'),
        ('Critical', 'Critical'),
    ]
    condition = models.CharField(max_length=200, choices=CONDITION_CHOICES, default='Normal')
    
    # --- THESE ARE THE NEW FIELDS YOU WANTED ---
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='patient_photos/', blank=True, null=True)
    # Blood Group (NEW FIELD)
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    # Height & Weight for monitoring display
    height = models.IntegerField(null=True, blank=True)  # cm
    weight = models.IntegerField(null=True, blank=True)  # kg
    # -------------------------------------------

    assigned_doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_device = models.CharField(max_length=100, default="Unassigned")
    is_active = models.BooleanField(default=True)
    start_time = models.DateTimeField(default=timezone.now)
    # Time-based progression: set when monitoring starts, cleared on stop/logout
    monitoring_started_at = models.DateTimeField(null=True, blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

ALERT_TYPE_CHOICES = [
    ('monitoring_status', 'Monitoring Status'),
    ('heart_rate_warning', 'Heart Rate Warning'),
    ('critical_health', 'Critical Health Alert'),
    ('oxygen_warning', 'Oxygen Warning'),
]

ALERT_SEVERITY_CHOICES = [
    ('normal', 'Normal'),
    ('warning', 'Warning'),
    ('critical', 'Critical'),
]

class Alert(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    bpm = models.IntegerField(null=True, blank=True)
    spo2 = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default="CRITICAL")
    # Feature 2: Structured alert fields
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES, default='monitoring_status')
    alert_severity = models.CharField(max_length=10, choices=ALERT_SEVERITY_CHOICES, default='normal')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"Alert for {self.patient.first_name}: {self.message} (BPM: {self.bpm}, SpO2: {self.spo2})"

class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    heart_rate = models.IntegerField()
    temperature = models.FloatField()
    oxygen_level = models.IntegerField()

    def __str__(self):
        return f"{self.patient.first_name} - {self.timestamp}"