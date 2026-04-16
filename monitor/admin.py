from django.contrib import admin
from .models import PatientVitals, HardwareConfig, HardwareStatus, MedicalReport


@admin.register(PatientVitals)
class PatientVitalsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'bpm', 'spo2', 'timestamp')
    readonly_fields = ('timestamp',)


@admin.register(HardwareConfig)
class HardwareConfigAdmin(admin.ModelAdmin):
    list_display = ('port', 'baud_rate', 'updated_at')
    readonly_fields = ('updated_at',)


@admin.register(HardwareStatus)
class HardwareStatusAdmin(admin.ModelAdmin):
    list_display = ('connected', 'last_seen')
    readonly_fields = ('last_seen',)


@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('patient', 'generated_by', 'summary', 'generated_at')
    readonly_fields = ('generated_at',)
