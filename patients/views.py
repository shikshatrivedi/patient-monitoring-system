from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient, PatientHistory

# --- 1. USER REGISTRATION (Creating an Account) ---
def register_user(request):
    """
    This handles the 'Create Account' page for new Doctors/Staff.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after signing up
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard') # Redirects directly to Dashboard
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})

# --- 2. DASHBOARD / PATIENT LIST ---
@login_required(login_url='login')
def patient_list(request):
    patients = Patient.objects.all().order_by('-start_time')
    return render(request, 'patient_list.html', {'patients': patients})

# --- 3. ADD PATIENT (The Form inside the Dashboard) ---
@login_required(login_url='login')
def add_patient(request):
    if request.method == "POST":
        # Capture Basic Info
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        blood_group = request.POST.get('blood_group')
        
        # Capture contact & email
        contact = request.POST.get('contact')
        email = request.POST.get('email')
        
        # Capture Clinical Info
        purpose = request.POST.get('purpose')
        department = request.POST.get('department')
        med_conditions = request.POST.get('medical_conditions')
        notes = request.POST.get('notes')
        
        # Vitals/Measurements
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        
        photo = request.FILES.get('photo')

        Patient.objects.create(
            first_name=first_name,
            last_name=last_name,
            age=age,
            gender=gender,
            blood_group=blood_group,
            phone=contact,            
            email=email,
            condition=purpose,
            department=department,
            medical_history=med_conditions,
            notes=notes,
            height=height,
            weight=weight,
            photo=photo,
            assigned_doctor=request.user,
            is_active=True,
            assigned_device="Arduino-Station-1"
        )
        messages.success(request, f"Patient {first_name} {last_name} registered successfully!")
        return redirect('dashboard')

    return render(request, 'premium_register.html', {'page_title': 'Register New Patient'})

# --- 4. EDIT PATIENT ---
@login_required(login_url='login')
def edit_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":
        patient.first_name = request.POST.get('first_name', patient.first_name)
        patient.last_name = request.POST.get('last_name', patient.last_name)
        patient.age = request.POST.get('age', patient.age)
        patient.gender = request.POST.get('gender', patient.gender)
        patient.blood_group = request.POST.get('blood_group', patient.blood_group)
        patient.phone = request.POST.get('phone', patient.phone)
        patient.email = request.POST.get('email', patient.email)
        patient.condition = request.POST.get('condition', patient.condition)
        patient.department = request.POST.get('department', patient.department)
        patient.medical_history = request.POST.get('medical_history', patient.medical_history)
        patient.notes = request.POST.get('notes', patient.notes)

        height = request.POST.get('height')
        weight = request.POST.get('weight')
        if height: patient.height = height
        if weight: patient.weight = weight

        # Handle photo update
        new_photo = request.FILES.get('photo')
        if new_photo:
            patient.photo = new_photo

        patient.save()
        messages.success(request, f"Patient {patient.first_name} {patient.last_name} updated successfully!")
        return redirect('dashboard')

    return render(request, 'add_patient.html', {
        'patient': patient,
        'edit_mode': True,
        'page_title': 'Edit Patient',
    })

# --- 5. DELETE PATIENT ---
@login_required(login_url='login')
def delete_patient(request, patient_id):
    if request.method == "POST":
        patient = get_object_or_404(Patient, id=patient_id)
        name = patient.full_name
        patient.delete()
        messages.success(request, f"Patient {name} deleted successfully.")
    return redirect('dashboard')

# --- 6. PATIENT HISTORY ---
@login_required(login_url='login')
def patient_history(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    history_records = PatientHistory.objects.filter(patient=patient).order_by('-timestamp')
    return render(request, 'history.html', {'patient': patient, 'history_records': history_records})