from django.urls import path
from . import views
from .api import get_live_data, get_vitals_history
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('logout/', views.custom_logout, name='logout'),

    # --- DASHBOARD & PATIENT MANAGEMENT ---
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('patients/', views.patient_list, name='patient_list'),
    
    path('patients/add/', views.add_patient, name='add_patient'),
    path('patients/history/<int:patient_id>/', views.patient_history, name='patient_history'),
    path('patients/toggle-monitor/<int:patient_id>/', views.toggle_monitoring, name='toggle_monitoring'),

    # Feature 1: Edit & Delete Patient
    path('patients/edit/<int:patient_id>/', views.edit_patient, name='edit_patient'),
    path('patients/delete/<int:patient_id>/', views.delete_patient, name='delete_patient'),

    # --- MONITORING & ALERTS ---
    path('monitor/live/<int:patient_id>/', views.monitor_patient, name='monitor_patient'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('reports/', views.reports_view, name='reports'),
    path('config/', views.settings_view, name='settings'),
    
    # Report Generation & Download
    path('report/<int:patient_id>/', views.generate_report, name='generate_report'),
    path('report/download/<int:report_id>/', views.download_report, name='download_report'),

    # API endpoints for live dashboard vitals polling
    path('api/live-data/', get_live_data, name='live_data'),
    path('api/vitals/', get_vitals_history, name='vitals_history'),

    # Feature 3 & 4: Admin Dashboard & Doctor Approval
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/approve/<int:doctor_id>/', views.approve_doctor, name='approve_doctor'),
    path('admin-panel/reject/<int:doctor_id>/', views.reject_doctor, name='reject_doctor'),

    # Hospital Reference Doctor Search (admin verification only)
    path('admin-panel/search-hospital-doctor/', views.search_hospital_doctor, name='search_hospital_doctor'),

    # Monitoring Page
    path('monitoring/', views.monitoring_view, name='monitoring'),
]

# Image/Media handling for Patient Photos
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)