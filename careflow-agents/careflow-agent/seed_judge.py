import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud import firestore as google_firestore
from datetime import datetime, timezone, timedelta
import os
import random

# Initialize with ADC
print("Initializing Firebase Admin with ADC...")
try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    app = firebase_admin.initialize_app(cred, {
        'projectId': 'careflow-478811',
    })

# Connect to specific database
print("Connecting to Firestore database: careflow-db")
db = google_firestore.Client(project='careflow-478811', database='careflow-db')

def seed_data():
    print("🚀 Starting Mega-Seed (15 Patients)...")
    
    # 1. Config Judge
    uid = "user_nurse_sarah"
    email = "judge-hackaton@careflow.demo"
    password = "JudgePassword123@"
    display_name = "Sarah Johnson, RN"
    hospital_id = "HOSP001"
    
    # Auth Logic (Judge)
    try:
        try:
            auth.get_user(uid)
            auth.update_user(uid, email=email, password=password, display_name=display_name)
        except auth.UserNotFoundError:
            auth.create_user(uid=uid, email=email, password=password, display_name=display_name)
        auth.set_custom_user_claims(uid, {"role": "nurse", "hospitalId": hospital_id, "department": "General Medicine"})
        print(f"✅ Auth User configured: {email}")
    except Exception as e:
        print(f"⚠️ Auth error: {e}")

    # 2. Patient Data Templates
    diagnoses = [
        ("Type 2 Diabetes", ["Metformin 500mg", "Glipizide 5mg"]),
        ("Congestive Heart Failure", ["Lisinopril 10mg", "Furosemide 40mg"]),
        ("COPD", ["Albuterol Inhaler", "Prednisone 20mg"]),
        ("Post-CABG Recovery", ["Aspirin 81mg", "Atorvastatin 40mg"]),
        ("Hypertension", ["Amlodipine 5mg", "Losartan 50mg"]),
        ("Pneumonia Recovery", ["Amoxicillin 875mg", "Guaifenesin 600mg"])
    ]
    
    risk_levels = ["safe", "safe", "safe", "safe", "warning", "warning", "critical"]
    names = [
        "Christ Chadrak MVOUNGOU", "Jean Dupont", "Marie Curie", "John Smith", "Elena Rodriguez",
        "Amani Khalid", "Yuki Tanaka", "Lucas Miller", "Sophie Martin", "Marcus Brown",
        "Isabella Rossi", "Chen Wei", "Amara Okafor", "Dmitry Volkov", "Sarah O'Connor"
    ]

    patient_ids = []

    # 3. Purge existing patients for this nurse to avoid mess (Optional but cleaner)
    # print("Purging old test data...")
    docs = db.collection("patients").where("assignedNurse.email", "==", email).stream()
    for doc in docs: doc.reference.delete()

    # 4. Create 15 patients
    for i, name in enumerate(names):
        p_id = f"p_h1_hack_{i:03d}"
        patient_ids.append(p_id)
        
        diag, meds = random.choice(diagnoses)
        risk = random.choice(risk_levels)
        
        # Create medication objects
        med_objs = [{
            "name": m, 
            "dosage": "As prescribed", 
            "frequency": "Daily", 
            "instructions": "Take with water",
            "scheduleHour": 8,
            "startDate": datetime.now(timezone.utc)
        } for m in meds]

        patient_data = {
            "id": p_id,
            "hospitalId": hospital_id,
            "name": name,
            "email": f"patient{i}@example.demo",
            "dateOfBirth": "1970-01-01",
            "contact": {"phone": f"+33744533{i:03d}", "preferredMethod": "phone"},
            "assignedNurse": {
                "name": display_name,
                "email": email,
                "phone": "+15559876543"
            },
            "dischargePlan": {
                "diagnosis": diag,
                "dischargeDate": datetime.now(timezone.utc) - timedelta(days=random.randint(1, 10)),
                "hospitalId": hospital_id,
                "dischargingPhysician": "Dr. Gemini Pro",
                "medications": med_objs,
                "criticalSymptoms": ["Severe pain", "Confusion", "Chest tightness"],
                "warningSymptoms": ["Fever", "Fatigue", "Dizziness"]
            },
            "nextAppointment": {
                "date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "type": "Routine Follow-up",
                "location": "Main Clinic"
            },
            "riskLevel": risk,
            "aiBrief": f"Patient recovering from {diag}. Risk level set to {risk} based on last automated round.",
            "status": "active",
            "lastAssessmentDate": datetime.now(timezone.utc)
        }
        
        db.collection("patients").document(p_id).set(patient_data)
        
        # Create a mock alert if not safe
        if risk != "safe":
            alert_id = f"alert_hack_{i:03d}"
            db.collection("alerts").document(alert_id).set({
                "id": alert_id,
                "patientId": p_id,
                "hospitalId": hospital_id,
                "patientName": name,
                "riskLevel": risk.upper(),
                "priority": "critical" if risk == "critical" else "warning",
                "status": "active",
                "aiBrief": f"Automated detection of potential complications related to {diag}.",
                "trigger": "Voice Check-in Analysis",
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc)
            })

    # 5. Update Nurse Profile with IDs
    user_data = {
        "userId": uid,
        "email": email,
        "name": display_name,
        "role": "nurse",
        "department": "Care Coordination",
        "hospitalId": hospital_id,
        "phone": "+15559876543",
        "assignedPatientIds": patient_ids,
        "preferences": {
            "notificationMethod": "both",
            "alertSound": True,
            "timezone": "America/New_York"
        },
        "createdAt": datetime.now(timezone.utc),
        "lastLoginAt": datetime.now(timezone.utc),
        "isActive": True,
    }
    db.collection("users").document(uid).set(user_data)
    
    print(f"✨ Mega-Seed Complete! 15 patients added to {display_name}'s list.")

if __name__ == "__main__":
    seed_data()
