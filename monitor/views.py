from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import re

from patients.models import Patient, Alert, PatientHistory
from monitor.models import PatientVitals, HardwareStatus, HardwareConfig, ActiveMonitoring, MedicalReport
from patients.forms import PatientRegistrationForm
from accounts.models import DoctorProfile

# PDF Report Generation Imports
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from django.db.models import Avg, Max, Min, Count, Exists, OuterRef


# ============================================================
# HELPER: Check if user is admin
# ============================================================

def is_admin_user(user):
    try:
        profile = DoctorProfile.objects.get(user=user)
        return profile.role == 'admin'
    except DoctorProfile.DoesNotExist:
        return user.is_superuser


def get_weekly_stats(patient):
    """
    Helper to compute Mon–Sun average HR and SpO2 for a patient.
    Returns a list of 7 dicts: {'day': str, 'avg_hr': float, 'avg_spo2': float}
    """
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_agg = {i: {'bpm_sum': 0, 'spo2_sum': 0, 'count': 0} for i in range(7)}

    week_vitals = PatientVitals.objects.filter(
        patient=patient,
        timestamp__gte=week_ago
    ).values('timestamp', 'bpm', 'spo2')

    for v in week_vitals:
        dow = v['timestamp'].weekday()
        day_agg[dow]['bpm_sum']  += v['bpm']
        day_agg[dow]['spo2_sum'] += v['spo2']
        day_agg[dow]['count']    += 1

    weekly_data = []
    for i in range(7):
        grp = day_agg[i]
        if grp['count'] > 0:
            avg_hr   = round(grp['bpm_sum']  / grp['count'], 1)
            avg_spo2 = round(grp['spo2_sum'] / grp['count'], 1)
        else:
            avg_hr   = None
            avg_spo2 = None
        weekly_data.append({'day': day_names[i], 'avg_hr': avg_hr, 'avg_spo2': avg_spo2})
    return weekly_data


# --- 1. USER REGISTRATION (Doctor Sign Up) ---

def register_user(request):
    """
    Handles the Custom Doctor Registration Form.
    """
    if request.method == "POST":
        # 1. Get data from your HTML form
        fullname = request.POST.get('fullname')
        username = request.POST.get('username')
        email = request.POST.get('mobile') # Storing mobile in email field for now
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # 2. Validations
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'register_user.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return render(request, 'register_user.html')

        # 3. Create the User
        # We split fullname to get First/Last name
        try:
            first_name, last_name = fullname.split(' ', 1)
        except ValueError:
            first_name = fullname
            last_name = ""

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email 
        )
        
        # 4. Success: Log them in immediately and go to Dashboard
        login(request, user)
        return redirect('dashboard')

    return render(request, 'register_user.html')


# --- 2. CUSTOM LOGIN (Doctor Log In) ---

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')
        
        user = authenticate(request, username=username_input, password=password_input)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
            
    return render(request, 'login.html')

def custom_logout(request):
    # Stop monitoring on logout — clear started_at so progression resets
    try:
        from monitor.models import ActiveMonitoring
        active_mon = ActiveMonitoring.get_active()
        if active_mon.active_patient:
            patient = active_mon.active_patient
            patient.monitoring_started_at = None
            patient.save()
            active_mon.active_patient = None
            active_mon.save()
    except Exception:
        pass
    logout(request)
    return redirect('login')


# --- 3. DASHBOARD & PATIENT VIEWS ---

@login_required(login_url='login')
def dashboard(request):
    # Obj 2: Admin/superuser must use admin dashboard
    if request.user.is_superuser or is_admin_user(request.user):
        return redirect('admin_dashboard')

    # Fetch active monitoring state
    active_mon = ActiveMonitoring.get_active()
    active_patient = active_mon.active_patient

    # Obj 5: Doctor sees only their own patients
    patients = Patient.objects.filter(is_active=True, assigned_doctor=request.user).order_by('-start_time')[:5]

    # --- Fetch real vitals and hardware status from database ---
    hw_status = HardwareStatus.get_status()
    
    # Connection logic: CONNECTED if last_seen < 5 seconds
    is_connected = False
    if hw_status.connected and hw_status.last_seen:
        diff = timezone.now() - hw_status.last_seen
        if diff.total_seconds() < 5:
            is_connected = True

    # Fetch latest vitals for active patient specifically
    vitals = None
    if active_patient:
        vitals = PatientVitals.objects.filter(patient=active_patient).order_by('-timestamp').first()

    context = {
        'total_patients': Patient.objects.filter(assigned_doctor=request.user).count(),
        'active_sessions': Patient.objects.filter(is_active=True, assigned_doctor=request.user).count(),
        'alerts_today': Alert.objects.filter(timestamp__date=timezone.now().date()).count(),
        'recent_patients': patients,
        'page_title': 'System Overview',
        # Active Monitoring Info
        'active_patient': active_patient,
        'hardware_connected': is_connected,
        'bpm': vitals.bpm if vitals else '--',
        'spo2': vitals.spo2 if vitals else '--',
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def add_patient(request):
    if request.method == "POST":
        # 1. Manual Strict Backend Validation
        required_posted = ['first_name', 'last_name', 'age', 'gender', 'blood_group', 'phone', 'email', 'condition', 'department']
        missing_fields = []
        for f in required_posted:
            if not request.POST.get(f) or request.POST.get(f).strip() == "":
                missing_fields.append(f.replace('_', ' ').capitalize())
        
        # Check photo specifically
        if 'photo' not in request.FILES:
            missing_fields.append('Profile Photo')
            
        if missing_fields:
            # Objective: If ANY required field is empty -> block submission
            messages.error(request, f"Required fields missing: {', '.join(missing_fields)}")
            form = PatientRegistrationForm(request.POST, request.FILES)
            return render(request, 'add_patient.html', {'form': form, 'page_title': 'Register New Subject'})
            
        # 2. Form Validation
        form = PatientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.start_time = timezone.now()
            patient.is_active = True
            patient.assigned_device = "Arduino-Station-1"
            patient.assigned_doctor = request.user # Assign current doctor
            patient.save()
            messages.success(request, "Patient successfully registered")
            form = PatientRegistrationForm() # Reset
            return render(request, 'add_patient.html', {'form': form, 'page_title': 'Register New Subject'})
        else:
            return render(request, 'add_patient.html', {'form': form, 'page_title': 'Register New Subject'})
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'add_patient.html', {'form': form, 'page_title': 'Register New Subject'})


@login_required(login_url='login')
def patient_list(request):
    # Obj 5: Admin sees all, doctor sees only their own
    if request.user.is_superuser or is_admin_user(request.user):
        patients = Patient.objects.all().order_by('-start_time')
    else:
        patients = Patient.objects.filter(assigned_doctor=request.user).order_by('-start_time')
    
    # Annotate each patient with whether they have vitals data and reports
    patients = patients.annotate(
        has_vitals=Exists(PatientVitals.objects.filter(patient=OuterRef('pk'))),
        has_reports=Count('reports')
    )
    
    active_mon = ActiveMonitoring.get_active()
    
    # Get Arduino hardware connection status for button state logic
    hw_status = HardwareStatus.get_status()
    hw_connected = hw_status.connected
    
    return render(request, 'patient_list.html', {
        'patients': patients, 
        'page_title': 'Patient Directory',
        'active_patient': active_mon.active_patient,
        'hw_connected': hw_connected,
    })

@login_required(login_url='login')
def toggle_monitoring(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    # Obj 6: Ownership check
    if not request.user.is_superuser and not is_admin_user(request.user):
        if patient.assigned_doctor != request.user:
            messages.error(request, "You do not have permission to access this patient.")
            return redirect('patient_list')
    active_mon = ActiveMonitoring.get_active()
    
    if active_mon.active_patient == patient:
        # Stop monitoring — clear the timer
        patient.monitoring_started_at = None
        patient.save()
        active_mon.active_patient = None
        messages.info(request, f"Stopped monitoring {patient.first_name}.")
    else:
        # Stop timer on previously monitored patient (if any)
        if active_mon.active_patient:
            prev = active_mon.active_patient
            prev.monitoring_started_at = None
            prev.save()
        # Start monitoring — record the start time
        patient.monitoring_started_at = timezone.now()
        patient.save()
        active_mon.active_patient = patient
        messages.success(request, f"Now monitoring {patient.first_name}.")
    
    active_mon.save()
    if active_mon.active_patient == patient:
        # We just started monitoring → redirect to monitoring page
        return redirect('monitoring')
    return redirect('patient_list')


# --- FEATURE 1: EDIT & DELETE PATIENT ---

@login_required(login_url='login')
def edit_patient(request, patient_id):
    """
    Edit an existing patient. Pre-fills the existing add_patient form with
    patient data, allows update, and redirects to patient list.
    """
    patient = get_object_or_404(Patient, id=patient_id)
    # Obj 6: Ownership check
    if not request.user.is_superuser and not is_admin_user(request.user):
        if patient.assigned_doctor != request.user:
            messages.error(request, "You do not have permission to access this patient.")
            return redirect('patient_list')

    if request.method == "POST":
        form = PatientRegistrationForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f"Patient {patient.first_name} {patient.last_name} updated successfully.")
            return redirect('patient_list')
    else:
        form = PatientRegistrationForm(instance=patient)

    return render(request, 'add_patient.html', {
        'form': form,
        'page_title': 'Edit Patient',
        'edit_mode': True,
        'patient': patient,
    })


@login_required(login_url='login')
def delete_patient(request, patient_id):
    """
    Delete a patient and all their related monitoring records.
    Only processes POST (triggered from JS confirmation popup).
    """
    patient = get_object_or_404(Patient, id=patient_id)
    # Obj 6: Ownership check
    if not request.user.is_superuser and not is_admin_user(request.user):
        if patient.assigned_doctor != request.user:
            messages.error(request, "You do not have permission to access this patient.")
            return redirect('patient_list')

    if request.method == "POST":
        patient_name = f"{patient.first_name} {patient.last_name}"

        # Stop active monitoring if this patient is being monitored
        active_mon = ActiveMonitoring.get_active()
        if active_mon.active_patient == patient:
            active_mon.active_patient = None
            active_mon.save()

        # CASCADE delete: PatientVitals, Alert, PatientHistory linked via FK
        patient.delete()

        messages.success(request, f"Patient '{patient_name}' and all related records have been deleted.")
        return redirect('patient_list')

    # If accessed via GET, just redirect to patient list
    return redirect('patient_list')


@login_required(login_url='login')
def alerts_view(request):
    alerts = Alert.objects.all().order_by('is_acknowledged', '-timestamp')
    return render(request, 'alerts.html', {'alerts': alerts, 'page_title': 'System Alerts'})

@login_required(login_url='login')
def settings_view(request):
    """
    GET  → Load current HardwareConfig and display settings page.
    POST → Save submitted COM port and baud rate to HardwareConfig.
    """
    config = HardwareConfig.get_config()

    if request.method == 'POST':
        port = request.POST.get('port', '').strip()
        baud_rate_str = request.POST.get('baud_rate', '').strip()

        if port:
            config.port = port
        if baud_rate_str.isdigit():
            config.baud_rate = int(baud_rate_str)

        config.save()
        messages.success(request, f'Configuration saved: {config.port} @ {config.baud_rate} baud')
        return redirect('settings')

    return render(request, 'settings.html', {
        'page_title': 'Hardware Configuration',
        'config': config,
    })

@login_required(login_url='login')
def reports_view(request):
    return render(request, 'reports.html', {'page_title': 'Data Reports'})

@login_required(login_url='login')
def monitor_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    # Obj 6: Ownership check
    if not request.user.is_superuser and not is_admin_user(request.user):
        if patient.assigned_doctor != request.user:
            messages.error(request, "You do not have permission to access this patient.")
            return redirect('patient_list')
    return render(request, 'monitor.html', {'patient': patient})

# --- HISTORY & REPORT GENERATION ---

@login_required(login_url='login')
def patient_history(request, patient_id):
    """
    View Frame (Patient History)
    ONLY show: Weekly data (Mon–Sun) and Past reports list
    """
    patient = get_object_or_404(Patient, id=patient_id)
    # Ownership check
    if not request.user.is_superuser and not is_admin_user(request.user):
        if patient.assigned_doctor != request.user:
            messages.error(request, "You do not have permission to accessz this patient.")
            return redirect('patient_list')
    
    weekly_data = get_weekly_stats(patient)
    saved_reports = MedicalReport.objects.filter(patient=patient).order_by('-generated_at')

    return render(request, 'history.html', {
        'patient': patient,
        'weekly_data': weekly_data,
        'saved_reports': saved_reports,
    })

@login_required(login_url='login')
def generate_report(request, patient_id):
    """
    Generates a professional medical report in PDF format for the given patient.
    Matches the exact 9-section structure requested by the user.
    """
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Ownership Check
    if not request.user.is_superuser and not is_admin_user(request.user):
        if patient.assigned_doctor != request.user:
            messages.error(request, "Access Denied: You are not authorized to view this report.")
            return redirect('patient_list')

    # 1. Gather Data
    doctor_name = request.user.get_full_name() or request.user.username
    doctor_id   = f"DOC-{request.user.id:04d}"  # fallback
    doctor_dept = "General Medicine"
    try:
        profile = DoctorProfile.objects.get(user=request.user)
        if profile.doctor_id:
            doctor_id = profile.doctor_id
    except Exception:
        pass

    # Monitoring Summary Data
    vitals_qs = PatientVitals.objects.filter(patient=patient)
    v_count = vitals_qs.count()
    is_active_mon = (patient.is_active and v_count > 0)
    mon_status = "Ongoing" if is_active_mon else "Monitoring Completed"
    
    stats = None
    vitals_impression = "Normal"
    if v_count > 0:
        stats = vitals_qs.aggregate(
            avg_bpm=Avg('bpm'), max_bpm=Max('bpm'), min_bpm=Min('bpm'),
            avg_spo2=Avg('spo2'), max_spo2=Max('spo2'), min_spo2=Min('spo2')
        )
        if stats['min_spo2'] < 95 or stats['max_bpm'] > 100 or stats['min_bpm'] < 60:
            vitals_impression = "Abnormal / Attention Required"

    # Alerts — for PDF
    alerts = Alert.objects.filter(patient=patient).order_by('-timestamp')
    warning_count  = alerts.filter(alert_severity='warning').count()
    critical_count = alerts.filter(alert_severity='critical').count()
    critical_alerts_count = critical_count  # kept for clinical assessment logic

    # 2. PDF Document Setup
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Professional Medical Styles
    styles.add(ParagraphStyle(name='MainTitle', parent=styles['Heading1'], fontSize=22, alignment=1, spaceAfter=20, textColor=colors.HexColor("#0f172a")))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=12, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#334155"), borderPadding=(2, 0, 2, 0), borderSide='bottom', borderColor=colors.lightgrey))
    styles.add(ParagraphStyle(name='DataLabel', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor("#64748b")))
    styles.add(ParagraphStyle(name='DataValue', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#1e293b")))
    styles.add(ParagraphStyle(name='AssessmentText', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Oblique'))
    styles.add(ParagraphStyle(name='FooterStyle', parent=styles['Normal'], fontSize=9, alignment=1, textColor=colors.HexColor("#64748b")))

    elements = []

    # --- Title ---
    elements.append(Paragraph("MEDICAL REPORT", styles['MainTitle']))
    elements.append(Spacer(1, 10))

    # --- Doctor Details ---
    elements.append(Paragraph("DOCTOR DETAILS", styles['SectionHeader']))
    doc_info = [
        [Paragraph("Doctor Name:", styles['DataLabel']), Paragraph(doctor_name, styles['DataValue'])],
        [Paragraph("Doctor ID:", styles['DataLabel']), Paragraph(doctor_id, styles['DataValue'])],
        [Paragraph("Department:", styles['DataLabel']), Paragraph(doctor_dept, styles['DataValue'])],
        [Paragraph("Report Date:", styles['DataLabel']), Paragraph(timezone.now().strftime("%d %b %Y, %H:%M %p"), styles['DataValue'])]
    ]
    t_doc = Table(doc_info, colWidths=[120, 350])
    t_doc.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_doc)

    # --- Patient Details ---
    elements.append(Paragraph("PATIENT DETAILS", styles['SectionHeader']))
    pat_info = [
        [Paragraph("Patient ID:", styles['DataLabel']), Paragraph(f"#{patient.id}", styles['DataValue']), Paragraph("Gender:", styles['DataLabel']), Paragraph(patient.gender, styles['DataValue'])],
        [Paragraph("Full Name:", styles['DataLabel']), Paragraph(patient.full_name, styles['DataValue']), Paragraph("Age:", styles['DataLabel']), Paragraph(str(patient.age), styles['DataValue'])],
        [Paragraph("Contact Number:", styles['DataLabel']), Paragraph(patient.phone or "N/A", styles['DataValue']), Paragraph("Email:", styles['DataLabel']), Paragraph(patient.email or "N/A", styles['DataValue'])],
        [Paragraph("Monitoring Purpose:", styles['DataLabel']), Paragraph(patient.condition or "N/A", styles['DataValue']), Paragraph("Department:", styles['DataLabel']), Paragraph(patient.department or "N/A", styles['DataValue'])],
    ]
    t_pat = Table(pat_info, colWidths=[100, 150, 80, 140])
    t_pat.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t_pat)

    # --- Monitoring Summary ---
    elements.append(Paragraph("MONITORING SUMMARY", styles['SectionHeader']))
    summary_text = [
        [Paragraph("Current Status:", styles['DataLabel']), Paragraph(mon_status, styles['DataValue'])],
        [Paragraph("Vital Impression:", styles['DataLabel']), Paragraph(vitals_impression, styles['DataValue'])]
    ]
    t_sum = Table(summary_text, colWidths=[120, 350])
    elements.append(t_sum)
    elements.append(Spacer(1, 8))

    if stats:
        v_data = [
            ["Vital Parameter", "Average", "Min", "Max"],
            ["Heart Rate (BPM)", f"{stats['avg_bpm']:.1f}", f"{stats['min_bpm']}", f"{stats['max_bpm']}"],
            ["Oxygen (SpO2 %)", f"{stats['avg_spo2']:.1f}%", f"{stats['min_spo2']}%", f"{stats['max_spo2']}%"]
        ]
        t_v = Table(v_data, colWidths=[150, 100, 100, 100])
        t_v.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        elements.append(t_v)

    # --- Alerts Section ---
    elements.append(Paragraph("ALERTS SECTION", styles['SectionHeader']))

    # Obj 9: Summary count line
    total_alerts = warning_count + critical_count
    if total_alerts > 0:
        summary_line = f"{warning_count} warning alert(s) and {critical_count} critical alert(s) detected during monitoring."
    else:
        summary_line = "No alerts detected during monitoring."
    elements.append(Paragraph(summary_line, styles['AssessmentText']))
    elements.append(Spacer(1, 6))

    if alerts.exists():
        # Structured per-alert table
        alert_data = [["Time", "Type", "Value", "Severity", "Message"]]
        for a in alerts[:8]:  # show up to 8 alerts
            bpm_val  = str(a.bpm)  if a.bpm  else "--"
            spo2_val = str(a.spo2) if a.spo2 else "--"
            val_str  = f"HR: {bpm_val} BPM" if "heart_rate" in (a.alert_type or "") else f"SpO2: {spo2_val}%"
            alert_data.append([
                a.timestamp.strftime("%I:%M %p"),
                (a.alert_type or "N/A").replace("_", " ").title(),
                val_str,
                (a.alert_severity or "N/A").capitalize(),
                a.message or "N/A",
            ])
        t_alert = Table(alert_data, colWidths=[55, 90, 70, 55, 200])
        t_alert.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN',      (0,0), (-1,-1), 'LEFT'),
            ('FONTSIZE',   (0,0), (-1,-1), 8),
            ('VALIGN',     (0,0), (-1,-1), 'TOP'),
        ]))
        elements.append(t_alert)
    else:
        elements.append(Paragraph("No alerts recorded for this patient.", styles['DataValue']))

    # --- Clinical Assessment ---
    elements.append(Paragraph("CLINICAL ASSESSMENT", styles['SectionHeader']))
    if v_count == 0:
        assess = "Insufficient monitoring data for a formal clinical assessment."
    elif critical_alerts_count > 0:
        assess = "The system recorded multiple critical violations. Patient shows signs of physiological instability requiring immediate clinical intervention and investigation of root causes for recurrent abnormal vitals."
    elif vitals_impression == "Normal":
        assess = "Patient's vital parameters remained within the physiological normal range throughout the monitoring period. No acute distress observed."
    else:
        assess = "Borderline vital signs observed. While not currently in acute failure, the patient warrants closer monitoring and evaluation of underlying compensatory mechanisms."
    elements.append(Paragraph(assess, styles['AssessmentText']))

    # --- Recommendations & Precautions ---
    elements.append(Paragraph("RECOMMENDATIONS", styles['SectionHeader']))
    rec = "Continue routine monitoring as prescribed. Maintain adequate hydration and rest."
    if vitals_impression != "Normal":
        rec = "Schedule immediate physician review. Increase vital sampling frequency. Monitor for associated symptoms like dizziness or chest pain."
    elements.append(Paragraph(rec, styles['DataValue']))

    elements.append(Paragraph("PRECAUTIONS / RESTRICTIONS", styles['SectionHeader']))
    pre = "No immediate restrictions. Normal activity as tolerated."
    if vitals_impression != "Normal":
        pre = "Restrict strenuous physical activity. Ensure portable monitoring is maintained if the patient is ambulatory."
    elements.append(Paragraph(pre, styles['DataValue']))

    # --- Final Impression ---
    elements.append(Paragraph("FINAL IMPRESSION", styles['SectionHeader']))
    imp = "Clinically stable." if vitals_impression == "Normal" else "Awaits specialist evaluation for vital sign volatility."
    elements.append(Paragraph(f"<b>{imp}</b>", styles['DataValue']))

    # Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<hr/>", styles['Normal']))
    elements.append(Paragraph("This is a computer-generated medical report summary from the LifeBeat Monitoring System.", styles['FooterStyle']))

    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    # Save report to database (Objective 7: Report Storage)
    from django.core.files.base import ContentFile
    report_filename = f"Medical_Report_{patient.first_name}_{patient.id}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    report_obj = MedicalReport(
        patient=patient,
        generated_by=request.user,
        summary=f"Report - {vitals_impression} - {v_count} vitals recorded"
    )
    report_obj.pdf_file.save(report_filename, ContentFile(pdf), save=True)
    
    # Return download response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_filename}"'
    response.write(pdf)

    # Mark report as generated for this session (Strict rule 8)
    session_key = f'report_generated_{patient.id}'
    request.session[session_key] = True

    return response


@login_required(login_url='login')
def download_report(request, report_id):
    """Serve a previously saved medical report PDF."""
    report = get_object_or_404(MedicalReport, id=report_id)
    # Ownership check
    if not request.user.is_superuser and not is_admin_user(request.user):
        if report.patient.assigned_doctor != request.user:
            messages.error(request, "Access denied.")
            return redirect('patient_list')
    
    response = HttpResponse(report.pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report.pdf_file.name.split("/")[-1]}"'
    return response


# ============================================================
# FEATURE 3 & 4: ADMIN DASHBOARD & DOCTOR APPROVAL
# ============================================================

def admin_required(view_func):
    """Decorator: only allows admin users."""
    from functools import wraps
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin_user(request.user):
            messages.error(request, "You do not have permission to access the admin area.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required(login_url='login')
@admin_required
def admin_dashboard(request):
    """
    Admin overview: all doctors, all patients, pending approvals, system alerts.
    """
    all_doctors = DoctorProfile.objects.select_related('user').filter(role='doctor')
    # Obj 1: Separate counts by status
    approved_doctors = all_doctors.filter(doctor_status='approved')
    pending_doctors = all_doctors.filter(doctor_status='pending')
    rejected_doctors = all_doctors.filter(doctor_status='rejected')
    all_patients = Patient.objects.all().order_by('-start_time')
    recent_alerts = Alert.objects.all().order_by('-timestamp')[:10]

    context = {
        'page_title': 'Admin Dashboard',
        'all_doctors': all_doctors,
        'pending_doctors': pending_doctors,
        'all_patients': all_patients,
        'recent_alerts': recent_alerts,
        'total_doctors': approved_doctors.count(),
        'pending_count': pending_doctors.count(),
        'rejected_count': rejected_doctors.count(),
        'total_patients': all_patients.count(),
        'total_alerts': Alert.objects.count(),
    }
    return render(request, 'admin_dashboard.html', context)


@login_required(login_url='login')
@admin_required
def approve_doctor(request, doctor_id):
    """Admin approves a doctor account."""
    profile = get_object_or_404(DoctorProfile, id=doctor_id)
    profile.doctor_status = 'approved'
    profile.approved_by_admin = request.user
    profile.save()
    messages.success(request, f"Doctor '{profile.user.username}' has been approved.")
    return redirect('admin_dashboard')


@login_required(login_url='login')
@admin_required
def reject_doctor(request, doctor_id):
    """Admin rejects a doctor account."""
    profile = get_object_or_404(DoctorProfile, id=doctor_id)
    profile.doctor_status = 'rejected'
    profile.save()
    messages.warning(request, f"Doctor '{profile.user.username}' has been rejected.")
    return redirect('admin_dashboard')


# ============================================================
# HOSPITAL REFERENCE DOCTOR SEARCH (Admin Only)
# Searches the HospitalReferenceDoctor reference table only.
# Does NOT touch DoctorProfile, User, or any system counts.
# ============================================================

@login_required(login_url='login')
@admin_required
def search_hospital_doctor(request):
    """
    JSON endpoint: search hospital reference doctor records by name.
    Returns up to 10 matching results.
    Used by admin dashboard search box for verification purposes.
    """
    from accounts.models import HospitalReferenceDoctor
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        qs = HospitalReferenceDoctor.objects.filter(name__icontains=query)[:10]
        results = list(qs.values('name', 'department', 'hospital_doc_id', 'specialization'))
    return JsonResponse({'results': results, 'query': query})


# ============================================================
# MONITORING PAGE VIEW
# ============================================================

@login_required(login_url='login')
def monitoring_view(request):
    """
    Monitoring page:
    - Blank if no patient selected
    - Full UI if a patient is selected (Arduino is OPTIONAL — falls back to SQLite)
    """
    from monitor.api import _get_indexed_vital

    active_mon = ActiveMonitoring.get_active()
    active_patient = active_mon.active_patient

    hw_status = HardwareStatus.get_status()
    is_connected = False
    if hw_status.connected and hw_status.last_seen:
        diff = timezone.now() - hw_status.last_seen
        if diff.total_seconds() < 5:
            is_connected = True

    # monitoring_active = patient IS selected (Arduino not required)
    monitoring_active = bool(active_patient)

    vitals_data    = []
    weekly_data    = []
    readings_count = 0
    saved_reports  = []
    initial_bpm    = None
    initial_spo2   = None

    if active_patient:
        readings_count = PatientVitals.objects.filter(patient=active_patient).count()

        vitals_qs = (
            PatientVitals.objects
            .filter(patient=active_patient)
            .order_by('-timestamp')[:100]
        )
        vitals_data = list(vitals_qs.values('bpm', 'spo2', 'timestamp'))
        vitals_data.reverse()

        weekly_data = get_weekly_stats(active_patient)

        saved_reports = list(
            MedicalReport.objects.filter(patient=active_patient)
            .order_by('-generated_at')
            .values('id', 'summary', 'generated_at')
        )

        # Initial vitals: use same logic as API so no jump on first poll
        if is_connected:
            latest = PatientVitals.objects.filter(
                patient=active_patient
            ).order_by('-timestamp').first()
            if latest and not (latest.bpm == 0 and latest.spo2 == 0):
                initial_bpm  = latest.bpm
                initial_spo2 = latest.spo2
        else:
            initial_bpm, initial_spo2 = _get_indexed_vital(active_patient)

    session_key = f'report_generated_{active_patient.id}' if active_patient else None
    report_sent = request.session.get(session_key, False) if session_key else False

    data_source_badge = "🟢 Live Arduino" if is_connected else "🟡 Demo Mode (SQLite Data)"

    import json
    return render(request, 'monitoring.html', {
        'page_title':         'Live Monitoring',
        'active_patient':     active_patient,
        'monitoring_active':  monitoring_active,
        'arduino_connected':  is_connected,
        'data_source_badge':  data_source_badge,
        'vitals_data':        json.dumps(vitals_data, default=str),
        'weekly_data':        json.dumps(weekly_data),
        'readings_count':     readings_count,
        'saved_reports':      saved_reports,
        'report_sent':        report_sent,
        'initial_bpm':        initial_bpm,
        'initial_spo2':       initial_spo2,
    })