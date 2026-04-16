from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import PatientVitals, HardwareStatus, ActiveMonitoring
from patients.models import Patient, Alert


# ============================================================
# ALERT CLASSIFICATION (mirrors hardware_bridge classify_vitals)
# Used for display purposes only — does NOT create Alert records.
# Alert records are exclusively created by hardware_bridge.py
# with debounce + cooldown.
# ============================================================

def classify_for_display(bpm, spo2):
    """
    Returns display-ready alert fields based on current vitals.
    Does NOT save to DB. DB writes are hardware_bridge's job.
    Returns: (alert_label, alert_type, alert_severity, alert_message)
    """
    hr_result   = None
    spo2_result = None

    # Heart Rate tiers
    if bpm < 50:
        hr_result = ("Critical Low Heart Rate", "heart_rate", "critical",
                     "Critical low heart rate. Immediate medical attention required.")
    elif bpm < 60:
        hr_result = ("Low Heart Rate", "heart_rate", "warning",
                     "Slightly low heart rate detected. Monitor patient condition.")
    elif bpm > 110:
        hr_result = ("Critical High Heart Rate", "heart_rate", "critical",
                     "Dangerously high heart rate. Immediate action required.")
    elif bpm > 100:
        hr_result = ("High Heart Rate", "heart_rate", "warning",
                     "Elevated heart rate detected. Observe patient.")

    # SpO2 tiers
    if spo2 < 92:
        spo2_result = ("Critical Oxygen Level", "spo2", "critical",
                       "Severely low oxygen level. Provide oxygen support immediately.")
    elif spo2 < 95:
        spo2_result = ("Low Oxygen Level", "spo2", "warning",
                       "Oxygen level slightly low. Monitor closely.")

    candidates = [r for r in [hr_result, spo2_result] if r is not None]

    if not candidates:
        return ("Normal", "monitoring_status", "normal", "Patient vitals are stable.")

    # Return critical over warning
    for c in candidates:
        if c[2] == "critical":
            return c
    return candidates[0]


def _get_indexed_vital(patient):
    """
    Time-based index progression through the seeded SQLite dataset.

    Logic:
      - Vitals are ordered oldest→newest (the seeded sequence).
      - elapsed_minutes = minutes since monitoring_started_at
      - index = (elapsed_minutes // 2) % total_records
      - This produces: record 0 at t=0, record 1 at t=2min, etc., looping.

    Returns (bpm, spo2) or (None, None) if no data exists.
    """
    from django.utils import timezone

    # All seeded vitals ordered oldest-first (the smooth sequence)
    vitals_qs = PatientVitals.objects.filter(
        patient=patient
    ).order_by('timestamp')

    total = vitals_qs.count()

    if total == 0:
        return None, None  # Edge case: no seeded data — UI stays clean

    # Compute elapsed minutes since monitoring began
    if patient.monitoring_started_at:
        elapsed_seconds = (timezone.now() - patient.monitoring_started_at).total_seconds()
        elapsed_minutes = max(0, int(elapsed_seconds // 60))
    else:
        # Fallback: just show the first record if no start time set
        elapsed_minutes = 0

    index = (elapsed_minutes // 2) % total
    record = vitals_qs[index]
    return record.bpm, record.spo2


@login_required
def get_live_data(request):
    """
    Returns real-time vitals for the active patient.

    Priority:
      1. Arduino ON  → use latest PatientVitals record (real sensor data)
      2. Arduino OFF → use time-based indexed progression through seeded SQLite data
         (simulates realistic 80→81→82→81→80 every 2 minutes)

    monitoring_active flag tells frontend whether alerts are live.
    """
    try:
        from django.utils import timezone

        hw_status = HardwareStatus.get_status()

        # Hardware connection check (last_seen < 5s)
        is_connected = False
        if hw_status.connected and hw_status.last_seen:
            diff = timezone.now() - hw_status.last_seen
            if diff.total_seconds() < 5:
                is_connected = True

        # Active patient
        active_mon = ActiveMonitoring.get_active()
        patient    = active_mon.active_patient

        if not patient:
            return JsonResponse({
                "bpm": None, "spo2": None,
                "status": "No Active Patient",
                "alert_label": "Monitoring Inactive",
                "alert_type": "monitoring_status",
                "alert_severity": "normal",
                "alert_message": "Select a patient to begin monitoring.",
                "system_health": "Connected ✅" if is_connected else "Disconnected ❌",
                "is_connected": is_connected,
                "monitoring_active": False,
                "data_source": "none",
            })

        if is_connected:
            # === ARDUINO ON: Use latest real sensor record ===
            vitals = PatientVitals.objects.filter(patient=patient).order_by('-timestamp').first()
            data_source = "live"
            data_source_badge = "🟢 Live Arduino"

            if not vitals or (vitals.bpm == 0 and vitals.spo2 == 0):
                bpm_val, spo2_val = None, None
            else:
                bpm_val  = vitals.bpm
                spo2_val = vitals.spo2
        else:
            # === ARDUINO OFF: Time-based sequential progression from SQLite ===
            bpm_val, spo2_val = _get_indexed_vital(patient)
            data_source = "sqlite"
            data_source_badge = "🟡 Demo Mode (SQLite Data)"

        if bpm_val is None or spo2_val is None:
            return JsonResponse({
                "bpm": None, "spo2": None,
                "status": "Waiting for data...",
                "alert_label": "Initialising",
                "alert_type": "monitoring_status",
                "alert_severity": "normal",
                "alert_message": "No vitals data found. Please seed the database.",
                "system_health": "Connected ✅" if is_connected else "Disconnected ❌",
                "is_connected": is_connected,
                "monitoring_active": True,
                "data_source": data_source,
                "data_source_badge": data_source_badge,
                "patient_name": f"{patient.first_name} {patient.last_name}",
            })

        # Classify for display
        alert_label, alert_type, alert_severity, alert_message = classify_for_display(
            bpm_val, spo2_val
        )

        # Value string for display
        if alert_type == "heart_rate":
            alert_value = f"BPM: {bpm_val}"
        elif alert_type == "spo2":
            alert_value = f"SpO2: {spo2_val}%"
        else:
            alert_value = f"HR {bpm_val} BPM | SpO2 {spo2_val}%"

        status_str = f"Monitoring: {patient.first_name}"
        if alert_severity == "critical":
            status_str = "⚠️ Critical"
        elif alert_severity == "warning":
            status_str = "⚠️ Warning"

        return JsonResponse({
            "bpm":              bpm_val,
            "spo2":             spo2_val,
            "status":           status_str,
            "alert_label":      alert_label,
            "alert_type":       alert_type,
            "alert_severity":   alert_severity,
            "alert_message":    alert_message,
            "alert_value":      alert_value,
            "system_health":    "Connected ✅" if is_connected else "Disconnected ❌",
            "is_connected":     is_connected,
            "monitoring_active": True,
            "data_source":      data_source,
            "data_source_badge": data_source_badge,
            "patient_name":     f"{patient.first_name} {patient.last_name}",
            "timestamp":        timezone.now().strftime("%I:%M %p"),
        })

    except Exception as e:
        return JsonResponse({
            "bpm": None, "spo2": None,
            "status": "Error",
            "alert_label": "System Error",
            "alert_type": "monitoring_status",
            "alert_severity": "normal",
            "alert_message": str(e),
            "system_health": "Unknown",
            "is_connected": False,
            "monitoring_active": False,
            "data_source": "error",
            "error": str(e),
        })


@login_required
def get_vitals_history(request):
    """
    Returns last 50 vitals for the active patient for graphing.
    """
    active_mon = ActiveMonitoring.get_active()
    patient    = active_mon.active_patient

    if not patient:
        return JsonResponse({"vitals": [], "status": "No Active Patient"})

    vitals_list = PatientVitals.objects.filter(patient=patient).order_by('-timestamp')[:50]

    data = []
    for v in reversed(list(vitals_list)):
        data.append({
            "timestamp": v.timestamp.strftime("%H:%M:%S"),
            "bpm":  v.bpm,
            "spo2": v.spo2,
        })

    return JsonResponse({
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "vitals": data,
    })
