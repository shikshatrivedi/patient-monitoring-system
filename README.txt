# 🏥 Patient Monitoring System

## 📌 Overview

The **Patient Monitoring System** is a software-based healthcare application designed to monitor patient vitals such as **Heart Rate (BPM)** and **SpO₂ (Oxygen Level)** in real-time.

The system simulates real-time patient data using a structured SQLite database, making it reliable for demonstration, testing, and academic purposes.

---

## 🎯 Objective

To develop a clean, user-friendly system that:

* Monitors patient health status
* Generates structured medical reports
* Provides intelligent alerts
* Simulates real-time data without dependency on hardware

---

## ⚙️ Technologies Used

* **Backend:** Python, Django
* **Frontend:** HTML, CSS
* **Database:** SQLite
* **Charts/Visualization:** JavaScript (for graphs)

---

## 👨‍⚕️ Key Features

### 🔐 Doctor Authentication System

* Doctor registration with ID verification
* Admin approval required before login
* Secure login system

---

### 🧑‍🤝‍🧑 Patient Management

* Add new patients with:

  * Name, Age, Gender
  * Blood Group (Compulsory)
  * Height, Weight
  * Medical Condition & Observations
* Profile completion tracking
* Patient photo upload (mandatory)

---

### 📊 Smart Monitoring Dashboard

* Dedicated **Monitoring Section**
* Displays:

  * Heart Rate (BPM)
  * SpO₂ Levels
* Patient details:

  * Age, Blood Group, Height, Weight
* Weekly activity visualization (Mon–Sun)

---

### 🔄 Real-Time Data Simulation (Demo Mode)

* Uses SQLite instead of hardware
* Smooth data transitions:

  * Example: 80 → 81 → 82 → 81
* Condition-based vitals:

  * Normal
  * Observation
  * Critical

---

### 🚨 Live Alert System

* Alerts generated based on thresholds:

  * Low/High Heart Rate
  * Low Oxygen Levels
* Includes:

  * Severity (Warning / Critical)
  * Timestamp
* Optional alert sound (beep)

---

### 📄 Report Generation

* Reports generated **only after monitoring**
* Includes:

  * Patient details
  * Monitoring duration
  * Vitals summary
  * Alerts summary
* Controlled generation (only once per session)

---

### 📁 Monitoring History

* Stores:

  * Weekly data
  * Previous reports
* Clean view if no data exists

---

### 🛡️ System Safety Features

* Monitoring stops automatically on logout
* No data = no report generation
* Prevents abnormal data jumps
* Clean fallback using database

---

## 🧠 System Logic (Core Idea)

* If hardware is unavailable → system switches to **SQLite-based simulation**
* Data is fetched dynamically and updated smoothly
* Monitoring works only when:

  * Patient is selected
  * System is active

---

## 🚀 How to Run the Project

```bash
# Step 1: Clone repository
git clone https://github.com/shikshatrivedi/patient-monitoring-system.git

# Step 2: Navigate to project
cd patient-monitoring-system

# Step 3: Create virtual environment
python -m venv venv

# Step 4: Activate environment
venv\Scripts\activate

# Step 5: Install dependencies
pip install -r requirements.txt

# Step 6: Run migrations
python manage.py migrate

# Step 7: Start server
python manage.py runserver
```

---

## 🔮 Future Scope

* Integration with real IoT devices
* Mobile application support
* Cloud-based monitoring
* AI-based health prediction

---

## 📌 Note

This project is designed primarily for **software-based simulation** with optional hardware support.

---

## 👩‍💻 Author

**Shiksha Trivedi**
