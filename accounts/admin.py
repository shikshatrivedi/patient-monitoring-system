from django.contrib import admin
from .models import DoctorProfile

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor_id', 'role', 'doctor_status', 'mobile_number')
    list_filter = ('doctor_status', 'role')
    list_editable = ('doctor_status',)
    search_fields = ('user__username', 'doctor_id', 'mobile_number')
