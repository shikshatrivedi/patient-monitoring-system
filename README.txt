==============================================================================
   💙 MEDI-MON: PC-BASED PATIENT MONITORING SYSTEM - USER MANUAL
==============================================================================

[1] SYSTEM STARTUP GUIDE
------------------------------------------------------------------------------
To run the full system, you must open TWO terminal windows.

STEP 1: Start the Web Server (Terminal 1)
   > cd PatientMonitoringSystem
   > python manage.py runserver
   (Keep this window open. Do not close it.)

STEP 2: Start the Hardware Bridge (Terminal 2)
   > cd PatientMonitoringSystem
   > python hardware_bridge.py
   (This script reads the Arduino/Sensor data.)

STEP 3: Access the System
   Open Browser: http://127.0.0.1:8000/
   
------------------------------------------------------------------------------
[2] DEFAULT CREDENTIALS (LOGIN)
------------------------------------------------------------------------------
Doctor Login:
   Username: [Your_Username]  (e.g., admin)
   Password: [Your_Password]  (e.g., DoctorPass123)

* If you forgot the password, use the "Forgot Password" link on the login page.
  (OTP will appear in the Terminal Window).

------------------------------------------------------------------------------
[3] HARDWARE CONNECTION GUIDE (Arduino Uno + MAX30102)
------------------------------------------------------------------------------
Pin Wiring:
   VCC  -->  5V
   GND  -->  GND
   SDA  -->  A4
   SCL  -->  A5

* Ensure the USB Cable is firmly connected to the Laptop.
* The system will AUTO-DETECT the COM port (Plug & Play).

------------------------------------------------------------------------------
[4] TROUBLESHOOTING & DEMO MODE
------------------------------------------------------------------------------
PROBLEM: "Hardware Disconnected" or Sensor wire broken.
SOLUTION: Enable Simulation Mode (Wizard Mode).

1. Open file: hardware_bridge.py
2. Change Line 19:
   FROM: DEMO_MODE = False
   TO:   DEMO_MODE = True
3. Restart the bridge script.
   (The system will now generate realistic fake data for presentation).

------------------------------------------------------------------------------
[5] VIVA CHEAT SHEET (Answers to Examiner Questions)
------------------------------------------------------------------------------
Q: How does the system get data from the sensor?
A: We use Serial Communication (USB-UART). The Arduino sends raw data string 
   "BPM,SpO2" which is intercepted by a Python script (PySerial library).

Q: What happens if the internet goes down?
A: Nothing. This is a Local PC-Based system (Localhost). It does not need internet.

Q: How do you handle invalid data (noise)?
A: I have a "Data Integrity Module" in Python that rejects impossible values 
   (e.g., SpO2 > 100% or BPM < 30).

Q: What if the Arduino is unplugged during monitoring?
A: The "System Health Module" detects the timeout (5 seconds) and immediately 
   alerts the dashboard with "HARDWARE OFFLINE".

Q: Where is the data stored?
A: In a local SQLite database using Django's ORM, ensuring data persistence.
==============================================================================