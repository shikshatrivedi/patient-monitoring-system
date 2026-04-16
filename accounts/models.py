from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('doctor', 'Doctor'),
    ('admin', 'Admin'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    # Feature 3 & 4: Role and approval system
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='doctor')
    doctor_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by_admin = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_doctors'
    )

    # Obj 7: Auto-generated Doctor ID (e.g. DOC001, DOC002)
    doctor_id = models.CharField(max_length=10, unique=True, blank=True, null=True)

    # Obj 2: Doctor ID Card upload (image or PDF)
    id_card = models.FileField(upload_to='doctor_id_cards/', blank=True, null=True)

    def is_admin(self):
        return self.role == 'admin'

    def is_approved(self):
        return self.doctor_status == 'approved'

    def __str__(self):
        return f"{self.user.username} ({self.role}) - {self.doctor_status}"


# ============================================================
# HOSPITAL REFERENCE DOCTOR DATABASE
# These are NOT system accounts. They are hospital employee
# reference records used ONLY for admin verification during
# doctor approval. They do not affect dashboard counts,
# login, or any other system feature.
# ============================================================

class HospitalReferenceDoctor(models.Model):
    name             = models.CharField(max_length=100)
    department       = models.CharField(max_length=100)
    hospital_doc_id  = models.CharField(max_length=20, unique=True)
    specialization   = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Hospital Reference Doctor"
        verbose_name_plural = "Hospital Reference Doctors"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.hospital_doc_id}] – {self.department}"