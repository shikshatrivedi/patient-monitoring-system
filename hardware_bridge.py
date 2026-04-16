import os
import django
import time
import random
import signal
import sys
from datetime import datetime

# ---------------- DJANGO SETUP ----------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from monitor.models import PatientVitals, HardwareConfig, HardwareStatus
from patients.models import Patient, Alert

# ---------------- LOGGING ----------------
LOG_FILE = "system_logs.txt"

def log_event(event_type, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{event_type}] {message}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass
    print(entry)


# ---------------- CONNECTION STATUS ----------------
def set_connected(state: bool):
    """Update HardwareStatus singleton in the database."""
    from django.utils import timezone
    hw = HardwareStatus.get_status()
    hw.connected = state
    if state:
        hw.last_seen = timezone.now()
    hw.save()


# ---------------- PORT DETECTION ----------------
def find_arduino_port(target_port: str):
    """
    Look for the configured target port first.
    Falls back to any port whose description contains 'Arduino' or 'CH340'.
    Returns None if nothing found.
    """
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if p.device == target_port:
                return target_port
        for p in ports:
            if "Arduino" in p.description or "CH340" in p.description:
                return p.device
    except Exception:
        pass
    return None


# ============================================================
# RICH ALERT CLASSIFICATION
# ============================================================
def classify_vitals(bpm, spo2):
    """
    Classifies vitals into alert tiers.
    HR (5 tiers): <50 critical | 50-59 warning | 60-100 normal | 101-110 warning | >110 critical
    SpO2 (3 tiers): <92 critical | 92-94 warning | >=95 normal
    Critical takes priority over warning.
    Returns (label, type_key, severity, message) or (None,)*4 if normal.
    """
    hr_result   = None
    spo2_result = None

    # --- Heart Rate ---
    if bpm < 50:
        hr_result = (
            "Critical Low Heart Rate", "heart_rate", "critical",
            "Critical low heart rate. Immediate medical attention required."
        )
    elif bpm < 60:
        hr_result = (
            "Low Heart Rate", "heart_rate", "warning",
            "Slightly low heart rate detected. Monitor patient condition."
        )
    elif bpm > 110:
        hr_result = (
            "Critical High Heart Rate", "heart_rate", "critical",
            "Dangerously high heart rate. Immediate action required."
        )
    elif bpm > 100:
        hr_result = (
            "High Heart Rate", "heart_rate", "warning",
            "Elevated heart rate detected. Observe patient."
        )

    # --- SpO2 ---
    if spo2 < 92:
        spo2_result = (
            "Critical Oxygen Level", "spo2", "critical",
            "Severely low oxygen level. Provide oxygen support immediately."
        )
    elif spo2 < 95:
        spo2_result = (
            "Low Oxygen Level", "spo2", "warning",
            "Oxygen level slightly low. Monitor closely."
        )

    candidates = [r for r in [hr_result, spo2_result] if r is not None]

    if not candidates:
        return None, None, None, None

    # Return critical first, then warning
    for c in candidates:
        if c[2] == "critical":
            return c
    return candidates[0]


# ============================================================
# DEBOUNCE + COOLDOWN STATE (in-memory per bridge session)
# ============================================================
consecutive_abnormal = {}  # {patient_id: {alert_type: count}}
last_alert_time      = {}  # {patient_id: {alert_type: epoch_float}}
DEBOUNCE_COUNT = 3          # consecutive abnormal readings before alert fires
COOLDOWN_SECS  = 60         # seconds before same alert type can fire again


def check_and_create_alert(patient, bpm, spo2):
    """
    Obj 1, 3, 4, 5, 7:
    - Evaluate vitals with rich classification
    - Apply debounce (3 consecutive abnormal readings)
    - Apply cooldown (60s between same alert type per patient)
    - Save Alert to DB only when both conditions pass
    - No alert when monitoring is stopped (called only from process_data)
    """
    pid = patient.id
    label, atype, sev, msg = classify_vitals(bpm, spo2)

    # Vitals are normal — reset debounce counters for this patient
    if label is None:
        if pid in consecutive_abnormal:
            consecutive_abnormal[pid] = {}
        return

    # Initialise per-patient tracking dicts
    consecutive_abnormal.setdefault(pid, {})
    last_alert_time.setdefault(pid, {})

    # Debounce: increment counter for this alert type
    count = consecutive_abnormal[pid].get(atype, 0) + 1
    consecutive_abnormal[pid][atype] = count

    if count < DEBOUNCE_COUNT:
        log_event("DEBOUNCE", f"{patient.first_name}: {label} — {count}/{DEBOUNCE_COUNT} readings")
        return

    # Cooldown: suppress if same alert fired too recently
    now_ts = time.time()
    last   = last_alert_time[pid].get(atype, 0)
    if (now_ts - last) < COOLDOWN_SECS:
        remaining = int(COOLDOWN_SECS - (now_ts - last))
        log_event("COOLDOWN", f"{patient.first_name}: {label} suppressed — {remaining}s cooldown remaining")
        return

    # All checks passed — save alert
    last_alert_time[pid][atype]      = now_ts
    consecutive_abnormal[pid][atype] = 0  # reset after firing

    value_str = f"BPM: {bpm}" if atype == "heart_rate" else f"SpO2: {spo2}%"

    Alert.objects.create(
        patient=patient,
        message=msg,
        bpm=bpm,
        spo2=spo2,
        status=sev.capitalize(),
        alert_type=atype,
        alert_severity=sev,
    )
    log_event("ALERT", f"[{sev.upper()}] {label} — {patient.first_name} | {value_str} | {msg}")
    print(f"🚨 ALERT [{sev.upper()}] {patient.first_name}: {label} — {value_str}")


# ---------------- DATA PROCESSING ----------------
def process_data(bpm, spo2, source="HARDWARE"):
    """
    Save incoming vitals to DB for the ACTIVE patient.
    Alerts run only when a patient is actively monitored (Obj 1 & 7).
    """
    try:
        from django.utils import timezone
        from monitor.models import ActiveMonitoring

        # Keep hardware heartbeat alive
        hw = HardwareStatus.get_status()
        hw.last_seen = timezone.now()
        hw.connected = True
        hw.save()

        active_mon = ActiveMonitoring.get_active()
        patient    = active_mon.active_patient

        if not patient:
            log_event("WARNING", "No active patient — vitals not saved")
            return

        PatientVitals.objects.create(patient=patient, bpm=bpm, spo2=spo2)
        log_event("DATA", f"Saved [{source}] {patient.first_name}: BPM={bpm}, SpO2={spo2}%")
        print(f"✅ {source} ({patient.first_name}): BPM={bpm}, SpO2={spo2}%")

        # Alert logic only fires here — guarantees alerts stop when monitoring stops
        check_and_create_alert(patient, bpm, spo2)

    except Exception as e:
        log_event("ERROR", f"process_data failed: {str(e)}")


# ---------------- SERIAL LINE PARSER ----------------
def parse_serial_line(line: str):
    """
    Format A: HR:72,SpO2:98
    Format B: 72,98
    """
    line = line.strip()
    if "HR:" in line and "SpO2:" in line:
        try:
            parts = line.split(',')
            return int(parts[0].split(':')[1]), int(parts[1].split(':')[1])
        except (IndexError, ValueError):
            return None, None
    parts = line.split(',')
    if len(parts) == 2:
        try:
            return int(parts[0].strip()), int(parts[1].strip())
        except ValueError:
            return None, None
    return None, None


# ============================================================
# SIMULATION LOOP
# Obj 2: Smooth ±1/±2 variation around a stable healthy baseline
# Baseline range: BPM 68–82, SpO2 95–99
# ============================================================
# ============================================================
# CONDITION-BASED BASELINE RANGES
# Normal: HR 78–85, SpO2 96–99
# Observation: HR 85–95, SpO2 93–96
# Critical: HR 95–110, SpO2 88–94
# ============================================================
CONDITION_BASELINES = {
    'Normal':      {'hr_min': 78,  'hr_max': 85,  'spo2_min': 96, 'spo2_max': 99},
    'Observation': {'hr_min': 85,  'hr_max': 95,  'spo2_min': 93, 'spo2_max': 96},
    'Critical':    {'hr_min': 95,  'hr_max': 110, 'spo2_min': 88, 'spo2_max': 94},
}

patient_baselines = {}  # {patient_id: {'hr': int, 'spo2': int, 'hr_min': int, 'hr_max': int, 'spo2_min': int, 'spo2_max': int}}

def run_bridge():
    # Mark as DISCONNECTED first — only show connected when bridge is truly running
    set_connected(False)
    log_event("INFO", "Hardware Bridge Started — Simulation Mode Active")

    # Graceful shutdown: mark disconnected when process exits
    def _shutdown(signum, frame):
        log_event("INFO", "Hardware Bridge stopping — setting Arduino DISCONNECTED")
        set_connected(False)
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Now mark connected — bridge is alive
    set_connected(True)
    log_event("SUCCESS", "Hardware status set to CONNECTED (simulation mode)")
    print("✅ Hardware Bridge CONNECTED — Simulation mode running")
    print("   Generating smooth condition-based vitals every 3 seconds...\n")

    try:
        while True:
            try:
                from monitor.models import ActiveMonitoring
                active_mon = ActiveMonitoring.get_active()
                patient    = active_mon.active_patient

                if patient:
                    pid = patient.id

                    # Assign condition-based baseline on first reading for this patient
                    if pid not in patient_baselines:
                        condition = patient.condition or 'Normal'
                        ranges = CONDITION_BASELINES.get(condition, CONDITION_BASELINES['Normal'])
                        bl_hr   = random.randint(ranges['hr_min'],   ranges['hr_max'])
                        bl_spo2 = random.randint(ranges['spo2_min'], ranges['spo2_max'])
                        patient_baselines[pid] = {
                            'hr':       bl_hr,
                            'spo2':     bl_spo2,
                            'hr_min':   ranges['hr_min'],
                            'hr_max':   ranges['hr_max'],
                            'spo2_min': ranges['spo2_min'],
                            'spo2_max': ranges['spo2_max'],
                        }
                        print(f"🆕 Baseline [{condition}] {patient.first_name}: HR={bl_hr}, SpO2={bl_spo2}%")

                    baseline = patient_baselines[pid]

                    # Smooth ±1 walk — clamped to condition range (no spikes)
                    hr_delta   = random.choice([-1, 0, 0, 1])
                    spo2_delta = random.choice([-1, 0, 0, 1])

                    new_hr   = baseline['hr']   + hr_delta
                    new_spo2 = baseline['spo2'] + spo2_delta

                    # Clamp within condition bounds
                    new_hr   = max(baseline['hr_min'],   min(baseline['hr_max'],   new_hr))
                    new_spo2 = max(baseline['spo2_min'], min(baseline['spo2_max'], new_spo2))

                    # Update stored current value so next tick walks from here
                    patient_baselines[pid]['hr']   = new_hr
                    patient_baselines[pid]['spo2'] = new_spo2

                    process_data(new_hr, new_spo2, "SIMULATED")

                else:
                    # No active patient — freeze alert state, keep HW alive
                    consecutive_abnormal.clear()
                    last_alert_time.clear()

                    from django.utils import timezone
                    hw = HardwareStatus.get_status()
                    hw.connected  = True
                    hw.last_seen  = timezone.now()
                    hw.save()
                    print("⏳ No active patient — alerts frozen, waiting...", end="\r", flush=True)

            except Exception as e:
                log_event("ERROR", f"Simulation loop error: {str(e)}")

            time.sleep(3)

    finally:
        # Always mark disconnected when bridge stops (covers crashes too)
        log_event("INFO", "Bridge loop ended — setting Arduino DISCONNECTED")
        set_connected(False)


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    run_bridge()
