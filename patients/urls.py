from django.urls import path
from . import views

urlpatterns = [
    # 1. Doctor Signup
    path('register/', views.register_user, name='patients_register'),

    # 2. Add Patient
    path('add/', views.add_patient, name='add_patient'),

    # 3. Edit Patient
    path('edit/<int:patient_id>/', views.edit_patient, name='edit_patient'),

    # 4. Delete Patient
    path('delete/<int:patient_id>/', views.delete_patient, name='delete_patient'),

    # 5. Dashboard
    path('dashboard/', views.patient_list, name='dashboard'),

    # 6. Patient History
    path('history/<int:patient_id>/', views.patient_history, name='patient_history'),
]